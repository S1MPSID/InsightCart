"""Data quality checks and source-to-database reconciliation.

Read-only. Nothing in this module writes to the database or alters the dataset.

Data quality
------------
Every check is an objective predicate evaluated against the live
`retail.fact_sales` table (and its three dimensions). Checks are computed with a
small number of aggregate queries - never by loading the 100,000 fact rows into
Python. A check is marked FAIL only when its predicate is genuinely violated;
no failure is assumed or injected.

Negative profit is deliberately reported as an informational check rather than a
defect: selling below cost is a legitimate business outcome (returns,
discounts, clearance), not a data quality error.

Reconciliation
--------------
The source totals are computed independently in Pandas directly from
`backend/scripts/sales.csv`. They are never read back out of PostgreSQL, so the
comparison is a genuine source-vs-target check. Differences are compared using
explicit, documented numeric tolerances.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.services.analytics_service import FACT_TABLE, AnalyticsError

logger = logging.getLogger(__name__)

DATE_DIM = "retail.dim_date"
PRODUCT_DIM = "retail.dim_products"
CUSTOMER_DIM = "retail.dim_customers"

# app/services -> app -> scripts, i.e. backend/scripts/sales.csv
_DEFAULT_SOURCE_CSV = Path(__file__).resolve().parents[2] / "sales.csv"

# Business columns that identify a distinct sales record (surrogate key excluded).
BUSINESS_KEY_COLUMNS = (
    "customer_id",
    "product_id",
    "date_id",
    "quantity",
    "sales_amount",
    "profit",
)

# --------------------------------------------------------------------------
# Tolerances for reconciliation
# --------------------------------------------------------------------------
# Money is compared as a float on both sides (CSV text -> float64 in Pandas,
# numeric -> float in the driver), so the last bits can differ. A one-cent
# absolute tolerance is far above that rounding noise yet still meaningful.
MONEY_TOLERANCE = 0.01
# Counts are integers on both sides and must agree exactly.
COUNT_TOLERANCE = 0


class SourceFileMissing(RuntimeError):
    """Raised when the CSV used as the reconciliation source cannot be read."""


def _source_csv_path() -> Path:
    configured = os.getenv("SOURCE_CSV_PATH", "").strip()
    return Path(configured) if configured else _DEFAULT_SOURCE_CSV


def _execute(sql: str, params: dict[str, Any] | None, label: str, db_engine: Engine | None) -> list[dict]:
    """Run one aggregate query and return list-of-dict rows."""
    active_engine = db_engine or engine
    try:
        with active_engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        logger.exception("%s query failed: %s", label, exc)
        raise AnalyticsError(f"Failed to load {label} from PostgreSQL.") from exc


def _check(
    name: str,
    description: str,
    value: int,
    status: Literal["PASS", "FAIL", "INFO"],
    explanation: str,
    details: dict | None = None,
) -> dict:
    return {
        "name": name,
        "description": description,
        "value": int(value),
        "status": status,
        "explanation": explanation,
        "details": details or {},
    }


# --------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------


def get_data_quality_report(db_engine: Engine | None = None) -> dict:
    """Run the data quality rule set and return a structured report.

    Uses three aggregate queries:
      1. row count, per-column null counts, invalid-sign counts, value ranges
      2. duplicate business records (grouped on all non-surrogate columns)
      3. orphaned dimension keys via LEFT JOIN ... IS NULL
    """
    # --- Query 1: counts, nulls, signs, ranges ---------------------------
    core = _execute(
        f"""
        SELECT
            COUNT(*)                                          AS row_count,
            COUNT(*) FILTER (WHERE sale_id IS NULL)           AS null_sale_id,
            COUNT(*) FILTER (WHERE customer_id IS NULL)       AS null_customer_id,
            COUNT(*) FILTER (WHERE product_id IS NULL)        AS null_product_id,
            COUNT(*) FILTER (WHERE date_id IS NULL)           AS null_date_id,
            COUNT(*) FILTER (WHERE quantity IS NULL)           AS null_quantity,
            COUNT(*) FILTER (WHERE sales_amount IS NULL)      AS null_sales_amount,
            COUNT(*) FILTER (WHERE profit IS NULL)            AS null_profit,
            COUNT(*) FILTER (WHERE quantity < 1)              AS invalid_quantity,
            COUNT(*) FILTER (WHERE sales_amount <= 0)         AS invalid_sales_amount,
            COUNT(*) FILTER (WHERE profit < 0)                AS negative_profit,
            MIN(quantity)                                     AS min_quantity,
            MAX(quantity)                                     AS max_quantity,
            MIN(sales_amount)                                 AS min_sales_amount,
            MAX(sales_amount)                                 AS max_sales_amount,
            MIN(profit)                                       AS min_profit,
            MAX(profit)                                       AS max_profit,
            COUNT(DISTINCT f.quantity)                        AS distinct_quantity,
            COUNT(DISTINCT f.sales_amount)                    AS distinct_sales_amount,
            COUNT(DISTINCT f.profit)                          AS distinct_profit
        FROM {FACT_TABLE} f
        """,
        None,
        "data quality core counts",
        db_engine,
    )[0]

    # --- Query 2: duplicate business records -----------------------------
    grouped_columns = ", ".join(BUSINESS_KEY_COLUMNS)
    duplicate_row_count = _execute(
        f"""
        SELECT COUNT(*) AS duplicate_groups
        FROM (
            SELECT 1
            FROM {FACT_TABLE} f
            GROUP BY {grouped_columns}
            HAVING COUNT(*) > 1
        ) duplicates
        """,
        None,
        "data quality duplicate detection",
        db_engine,
    )[0]["duplicate_groups"]

    # --- Query 3: orphaned dimension keys --------------------------------
    orphans = _execute(
        f"""
        SELECT
            COUNT(*) FILTER (WHERE c.customer_id IS NULL)  AS orphaned_customers,
            COUNT(*) FILTER (WHERE p.product_id IS NULL)   AS orphaned_products,
            COUNT(*) FILTER (WHERE d.date_id IS NULL)      AS orphaned_dates
        FROM {FACT_TABLE} f
        LEFT JOIN {CUSTOMER_DIM} c ON c.customer_id = f.customer_id
        LEFT JOIN {PRODUCT_DIM}  p ON p.product_id  = f.product_id
        LEFT JOIN {DATE_DIM}     d ON d.date_id      = f.date_id
        """,
        None,
        "data quality orphan detection",
        db_engine,
    )[0]

    row_count = int(core["row_count"] or 0)
    checks: list[dict] = []

    # --- Structural ------------------------------------------------------
    checks.append(
        _check(
            "fact_row_count",
            "Total number of rows in retail.fact_sales.",
            row_count,
            "PASS" if row_count > 0 else "FAIL",
            f"fact_sales contains {row_count:,} rows."
            if row_count > 0
            else "fact_sales is empty, so no analytics can be produced.",
        )
    )

    duplicate_groups = int(duplicate_row_count or 0)
    checks.append(
        _check(
            "duplicate_business_records",
            "Groups of rows sharing identical values across all business columns "
            "(surrogate key sale_id excluded).",
            duplicate_groups,
            "PASS" if duplicate_groups == 0 else "FAIL",
            "No duplicate business records were found."
            if duplicate_groups == 0
            else f"{duplicate_groups:,} group(s) of duplicate business records were found.",
        )
    )

    # --- Nulls -----------------------------------------------------------
    null_specs = [
        ("null_sale_id", "sale_id"),
        ("null_customer_id", "customer_id"),
        ("null_product_id", "product_id"),
        ("null_date_id", "date_id"),
        ("null_quantity", "quantity"),
        ("null_sales_amount", "sales_amount"),
        ("null_profit", "profit"),
    ]
    for check_name, column_name in null_specs:
        nulls = int(core[check_name] or 0)
        checks.append(
            _check(
                check_name,
                f"Rows where {column_name} is NULL.",
                nulls,
                "PASS" if nulls == 0 else "FAIL",
                f"{column_name} is fully populated."
                if nulls == 0
                else f"{nulls:,} row(s) have a NULL {column_name}.",
            )
        )

    # --- Value validity --------------------------------------------------
    invalid_quantity = int(core["invalid_quantity"] or 0)
    checks.append(
        _check(
            "invalid_quantity",
            "Rows where quantity is less than 1 (zero or negative units).",
            invalid_quantity,
            "PASS" if invalid_quantity == 0 else "FAIL",
            "Every row records at least one unit."
            if invalid_quantity == 0
            else f"{invalid_quantity:,} row(s) have a non-positive quantity.",
        )
    )

    invalid_sales = int(core["invalid_sales_amount"] or 0)
    checks.append(
        _check(
            "invalid_sales_amount",
            "Rows where sales_amount is zero or negative.",
            invalid_sales,
            "PASS" if invalid_sales == 0 else "FAIL",
            "Every row has a positive sales amount."
            if invalid_sales == 0
            else f"{invalid_sales:,} row(s) have a non-positive sales amount.",
        )
    )

    # Negative profit is valid business data, not a defect, so this is INFO.
    negative_profit = int(core["negative_profit"] or 0)
    checks.append(
        _check(
            "negative_profit_records",
            "Rows where profit is negative. Reported for visibility only: selling "
            "below cost (returns, discounts, clearance) is a legitimate outcome "
            "and is NOT treated as a data quality defect.",
            negative_profit,
            "INFO",
            f"{negative_profit:,} row(s) report a loss. This is expected business "
            "behaviour and does not fail the data quality gate."
            if negative_profit > 0
            else "No loss-making rows are present in this dataset.",
        )
    )

    # --- Referential integrity -------------------------------------------
    orphan_specs = [
        ("orphaned_customer_id", "customer_id", "dim_customers", orphans["orphaned_customers"]),
        ("orphaned_product_id", "product_id", "dim_products", orphans["orphaned_products"]),
        ("orphaned_date_id", "date_id", "dim_date", orphans["orphaned_dates"]),
    ]
    for check_name, column_name, dim_table, value in orphan_specs:
        orphan_count = int(value or 0)
        checks.append(
            _check(
                check_name,
                f"Fact rows whose {column_name} has no matching row in retail.{dim_table}.",
                orphan_count,
                "PASS" if orphan_count == 0 else "FAIL",
                f"Every {column_name} resolves to a row in {dim_table}."
                if orphan_count == 0
                else f"{orphan_count:,} fact row(s) reference a missing {column_name}.",
            )
        )

    # --- Observed ranges (informational) ----------------------------------
    # `value` is the number of distinct values observed; min/max carry the range.
    for check_name, description, column_name in [
        ("quantity_range", "Distinct quantity values observed, with range.", "quantity"),
        ("sales_amount_range", "Distinct sales_amount values observed, with range.", "sales_amount"),
        ("profit_range", "Distinct profit values observed, with range.", "profit"),
    ]:
        low = core[f"min_{column_name}"]
        high = core[f"max_{column_name}"]
        distinct = int(core[f"distinct_{column_name}"] or 0)
        checks.append(
            _check(
                check_name,
                description,
                distinct,
                "INFO",
                f"Observed {column_name} range: {low} to {high}.",
                details={
                    "min": float(low) if low is not None else None,
                    "max": float(high) if high is not None else None,
                    "distinct_values": distinct,
                },
            )
        )

    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    info = sum(1 for c in checks if c["status"] == "INFO")

    return {
        "generated_at": datetime.now(timezone.utc),
        "table": FACT_TABLE,
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "informational": info,
        "overall_status": "FAIL" if failed else "PASS",
        "checks": checks,
    }


# --------------------------------------------------------------------------
# Reconciliation
# --------------------------------------------------------------------------


def _reconciliation_metric(
    metric: str,
    source_value: float,
    database_value: float,
    tolerance: float,
    source_label: str,
    database_label: str,
) -> dict:
    difference = float(source_value) - float(database_value)
    status: Literal["PASS", "FAIL"] = "PASS" if abs(difference) <= tolerance else "FAIL"
    if tolerance == 0:
        rule = "exact match required"
    else:
        rule = f"absolute difference must be <= {tolerance}"
    return {
        "metric": metric,
        "source_value": source_value,
        "database_value": database_value,
        "difference": round(difference, 6),
        "tolerance": tolerance,
        "status": status,
        "note": (
            f"{source_label} vs {database_label}; {rule}. "
            f"Observed difference {round(difference, 6)}."
        ),
    }


def get_reconciliation_report(db_engine: Engine | None = None) -> dict:
    """Compare independently computed Pandas totals against PostgreSQL totals.

    The source values come straight from the CSV via Pandas and are never read
    from the database, so this is a real source-to-target reconciliation.
    """
    csv_path = _source_csv_path()
    if not csv_path.exists():
        logger.error("Reconciliation source file missing: %s", csv_path)
        raise SourceFileMissing(f"Source file not found: {csv_path}")

    try:
        frame = pd.read_csv(csv_path)
    except Exception as exc:  # pandas raises a variety of parser/IO errors
        logger.exception("Could not read source file %s: %s", csv_path, exc)
        raise SourceFileMissing(f"Source file could not be read: {csv_path}") from exc

    missing_columns = [
        column
        for column in ("quantity", "sales_amount", "profit")
        if column not in frame.columns
    ]
    if missing_columns:
        logger.error("Source file is missing columns: %s", missing_columns)
        raise SourceFileMissing(
            f"Source file is missing required columns: {', '.join(missing_columns)}"
        )

    # --- Independent source totals (Pandas, straight from the CSV) --------
    source_transactions = int(len(frame))
    source_quantity = int(frame["quantity"].sum())
    source_revenue = float(frame["sales_amount"].sum())
    source_profit = float(frame["profit"].sum())

    # --- Independent database totals (single SQL aggregate) --------------
    db_row = _execute(
        f"""
        SELECT
            COUNT(*)                          AS transactions,
            COALESCE(SUM(f.quantity), 0)      AS quantity,
            COALESCE(SUM(f.sales_amount), 0)  AS revenue,
            COALESCE(SUM(f.profit), 0)        AS profit
        FROM {FACT_TABLE} f
        """,
        None,
        "reconciliation database totals",
        db_engine,
    )[0]

    source_label = f"Pandas sum/count over {csv_path.name}"
    database_label = f"PostgreSQL aggregate over {FACT_TABLE}"

    metrics = [
        _reconciliation_metric(
            "Transaction count",
            source_transactions,
            int(db_row["transactions"] or 0),
            COUNT_TOLERANCE,
            source_label,
            database_label,
        ),
        _reconciliation_metric(
            "Quantity",
            source_quantity,
            int(db_row["quantity"] or 0),
            COUNT_TOLERANCE,
            source_label,
            database_label,
        ),
        _reconciliation_metric(
            "Revenue",
            round(source_revenue, 2),
            round(float(db_row["revenue"] or 0), 2),
            MONEY_TOLERANCE,
            source_label,
            database_label,
        ),
        _reconciliation_metric(
            "Profit",
            round(source_profit, 2),
            round(float(db_row["profit"] or 0), 2),
            MONEY_TOLERANCE,
            source_label,
            database_label,
        ),
    ]

    passed = sum(1 for m in metrics if m["status"] == "PASS")
    failed = sum(1 for m in metrics if m["status"] == "FAIL")

    return {
        "generated_at": datetime.now(timezone.utc),
        "source": source_label,
        "database": database_label,
        "source_file": csv_path.name,
        "tolerance_policy": (
            f"Counts must match exactly (tolerance {COUNT_TOLERANCE}); "
            f"monetary totals use a {MONEY_TOLERANCE} absolute tolerance to absorb "
            "floating point rounding between CSV text, Pandas float64 and "
            "PostgreSQL numeric."
        ),
        "total_metrics": len(metrics),
        "passed": passed,
        "failed": failed,
        "overall_status": "FAIL" if failed else "PASS",
        "metrics": metrics,
    }
