"""Rule-based transaction exception detection.

Read-only. No data is modified and nothing is fabricated: if the dataset contains
no exceptions, the endpoint reports zero.

Methodology
-----------
Thresholds are *derived from the dataset* rather than hardcoded, using Tukey's
fences on the interquartile range:

    upper fence = Q3 + 1.5 * IQR      (medium severity band)
    high  fence = Q3 + 3.0 * IQR      (high severity band)
    lower fence = Q1 - 1.5 * IQR      (for profit margin only)

Q1 and Q3 are the 25th and 75th percentiles, computed with percentile_cont in
PostgreSQL. The resulting bounds are passed into the detection query as bound
parameters, so the SQL stays a single pass and no user input reaches the query
text.

These rules identify *unusual* records only. A flagged transaction is NOT a
finding of fraud, error or wrongdoing - it is simply a row that sits outside the
expected statistical range and is worth reviewing.

Severity
--------
    critical  invalid_transaction_values  (a data-integrity violation)
    high      value beyond the 3.0 x IQR fence
    medium    value beyond the 1.5 x IQR fence
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.services.analytics_service import DATE_DIM, FACT_TABLE, AnalyticsError

logger = logging.getLogger(__name__)

IQR_MULTIPLIER = 1.5
IQR_HIGH_MULTIPLIER = 3.0

Severity = Literal["critical", "high", "medium"]

METHOD_DESCRIPTION = (
    "Tukey fences on the interquartile range. Thresholds are computed from the "
    "data at request time with PostgreSQL percentile_cont: an exception is a "
    "value beyond Q3 + 1.5*IQR (medium) or Q3 + 3.0*IQR (high). Profit margin "
    "is also checked against the lower fence Q1 - 1.5*IQR. Invalid values "
    "(non-positive quantity or sales amount, or NULL keys) are critical. "
    "Flags indicate statistical unusualness only and are not evidence of fraud."
)

RULES_DOCUMENTATION = [
    {
        "rule_id": "unusually_high_sales_amount",
        "description": "sales_amount above the upper Tukey fence for the column.",
        "severity": "medium, or high beyond the 3.0 x IQR fence",
    },
    {
        "rule_id": "unusually_high_quantity",
        "description": "quantity above the upper Tukey fence for the column.",
        "severity": "medium, or high beyond the 3.0 x IQR fence",
    },
    {
        "rule_id": "unusually_high_profit",
        "description": "profit above the upper Tukey fence for the column.",
        "severity": "medium, or high beyond the 3.0 x IQR fence",
    },
    {
        "rule_id": "extreme_profit_margin",
        "description": (
            "Per-transaction profit margin (profit / sales_amount * 100) outside "
            "the lower or upper Tukey fence."
        ),
        "severity": "medium, or high beyond the 3.0 x IQR fence",
    },
    {
        "rule_id": "invalid_transaction_values",
        "description": (
            "Non-positive quantity or sales_amount, a NULL key or measure, or a "
            "date_id that does not resolve in retail.dim_date."
        ),
        "severity": "critical",
    },
]

# Bounds query: Q1/Q3 for each rule metric in one pass over the fact table.
_BOUNDS_SQL = text(
    f"""
    SELECT
        percentile_cont(0.25) WITHIN GROUP (ORDER BY f.sales_amount) AS sales_q1,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY f.sales_amount) AS sales_q3,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY f.quantity)     AS qty_q1,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY f.quantity)     AS qty_q3,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY f.profit)       AS profit_q1,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY f.profit)       AS profit_q3,
        percentile_cont(0.25) WITHIN GROUP (
            ORDER BY CASE WHEN f.sales_amount > 0
                          THEN f.profit / f.sales_amount * 100.0 END
        ) AS margin_q1,
        percentile_cont(0.75) WITHIN GROUP (
            ORDER BY CASE WHEN f.sales_amount > 0
                          THEN f.profit / f.sales_amount * 100.0 END
        ) AS margin_q3
    FROM {FACT_TABLE} f
    """
)

# Detection query. Thresholds arrive as bound parameters, never as SQL text.
# Returns one row per flagged transaction with a boolean per rule, plus exact
# global counts per rule via window aggregates (computed before LIMIT).
_DETECTION_SQL = text(
    f"""
    SELECT
        t.sale_id,
        t.customer_id,
        t.product_id,
        t.full_date,
        t.quantity,
        t.sales_amount,
        t.profit,
        t.margin,
        t.invalid_detail,
        t.is_invalid,
        t.high_sales,
        t.high_qty,
        t.high_profit,
        t.extreme_margin,
        COUNT(*) OVER ()                                        AS total_flagged,
        COUNT(*) FILTER (WHERE t.high_sales)     OVER ()         AS total_high_sales,
        COUNT(*) FILTER (WHERE t.high_qty)       OVER ()         AS total_high_qty,
        COUNT(*) FILTER (WHERE t.high_profit)    OVER ()         AS total_high_profit,
        COUNT(*) FILTER (WHERE t.extreme_margin) OVER ()         AS total_extreme_margin,
        COUNT(*) FILTER (WHERE t.is_invalid)     OVER ()         AS total_invalid
    FROM (
        SELECT
            f.sale_id,
            f.customer_id,
            f.product_id,
            d.full_date,
            f.quantity,
            f.sales_amount,
            f.profit,
            CASE WHEN f.sales_amount > 0
                 THEN f.profit / f.sales_amount * 100.0 END AS margin,
            concat_ws('; ',
                CASE WHEN f.quantity IS NULL OR f.quantity < 1
                     THEN 'quantity=' || coalesce(f.quantity::text, 'NULL') END,
                CASE WHEN f.sales_amount IS NULL OR f.sales_amount <= 0
                     THEN 'sales_amount=' || coalesce(f.sales_amount::text, 'NULL') END,
                CASE WHEN f.profit IS NULL
                     THEN 'profit=NULL' END,
                CASE WHEN f.customer_id IS NULL
                     THEN 'customer_id=NULL' END,
                CASE WHEN f.product_id IS NULL
                     THEN 'product_id=NULL' END,
                CASE WHEN f.date_id IS NULL OR d.date_id IS NULL
                     THEN 'date_id=NULL or unresolvable in dim_date' END
            ) AS invalid_detail,
            (f.quantity IS NULL OR f.quantity < 1
             OR f.sales_amount IS NULL OR f.sales_amount <= 0
             OR f.profit IS NULL OR f.customer_id IS NULL
             OR f.product_id IS NULL OR f.date_id IS NULL
             OR d.date_id IS NULL)                         AS is_invalid,
            (f.sales_amount > :sales_upper)                AS high_sales,
            (f.quantity > :qty_upper)                      AS high_qty,
            (f.profit > :profit_upper)                    AS high_profit,
            ((f.sales_amount > 0 AND f.profit / f.sales_amount * 100.0 > :margin_upper)
             OR (f.sales_amount > 0 AND f.profit / f.sales_amount * 100.0 < :margin_lower))
                                                             AS extreme_margin
        FROM {FACT_TABLE} f
        LEFT JOIN {DATE_DIM} d ON d.date_id = f.date_id
        WHERE f.sales_amount > :sales_upper
           OR f.quantity > :qty_upper
           OR f.profit > :profit_upper
           OR (f.sales_amount > 0 AND (f.profit / f.sales_amount * 100.0 > :margin_upper
                                     OR f.profit / f.sales_amount * 100.0 < :margin_lower))
           OR f.quantity IS NULL OR f.quantity < 1
           OR f.sales_amount IS NULL OR f.sales_amount <= 0
           OR f.profit IS NULL OR f.customer_id IS NULL
           OR f.product_id IS NULL OR f.date_id IS NULL OR d.date_id IS NULL
        ORDER BY f.sale_id
    ) t
    ORDER BY t.sale_id
    LIMIT :row_limit
    """
)


class ExceptionAnalysisError(RuntimeError):
    """Raised when exception analysis cannot be completed."""


def _execute(sql, params, label, db_engine: Engine | None):
    active_engine = db_engine or engine
    try:
        with active_engine.connect() as connection:
            result = connection.execute(sql, params or {})
            return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        logger.exception("%s query failed: %s", label, exc)
        raise ExceptionAnalysisError(f"Failed to load {label} from PostgreSQL.") from exc


def _fence_bounds(q1: float, q3: float) -> tuple[float, float, float]:
    """Return (iqr, upper_fence, high_fence) for a quartile pair."""
    iqr = float(q3) - float(q1)
    return iqr, float(q3) + IQR_MULTIPLIER * iqr, float(q3) + IQR_HIGH_MULTIPLIER * iqr


def _round(value: Any, places: int = 2) -> float:
    return None if value is None else round(float(value), places)


def _build_thresholds(bounds_row: dict) -> dict:
    """Derive every threshold from the measured quartiles."""
    sales_iqr, sales_upper, sales_high = _fence_bounds(bounds_row["sales_q1"], bounds_row["sales_q3"])
    qty_iqr, qty_upper, qty_high = _fence_bounds(bounds_row["qty_q1"], bounds_row["qty_q3"])
    profit_iqr, profit_upper, profit_high = _fence_bounds(bounds_row["profit_q1"], bounds_row["profit_q3"])
    margin_iqr, margin_upper, margin_high = _fence_bounds(bounds_row["margin_q1"], bounds_row["margin_q3"])
    margin_lower = float(bounds_row["margin_q1"]) - IQR_MULTIPLIER * margin_iqr
    margin_lower_high = float(bounds_row["margin_q1"]) - IQR_HIGH_MULTIPLIER * margin_iqr

    return {
        "sales_amount": {
            "q1": _round(bounds_row["sales_q1"]),
            "q3": _round(bounds_row["sales_q3"]),
            "iqr": _round(sales_iqr),
            "upper_fence": _round(sales_upper),
            "high_fence": _round(sales_high),
        },
        "quantity": {
            "q1": _round(bounds_row["qty_q1"]),
            "q3": _round(bounds_row["qty_q3"]),
            "iqr": _round(qty_iqr),
            "upper_fence": _round(qty_upper),
            "high_fence": _round(qty_high),
        },
        "profit": {
            "q1": _round(bounds_row["profit_q1"]),
            "q3": _round(bounds_row["profit_q3"]),
            "iqr": _round(profit_iqr),
            "upper_fence": _round(profit_upper),
            "high_fence": _round(profit_high),
        },
        "profit_margin_pct": {
            "q1": _round(bounds_row["margin_q1"]),
            "q3": _round(bounds_row["margin_q3"]),
            "iqr": _round(margin_iqr),
            "lower_fence": _round(margin_lower),
            "lower_high_fence": _round(margin_lower_high),
            "upper_fence": _round(margin_upper),
            "high_fence": _round(margin_high),
        },
    }


def _band_severity(value: float, upper_fence: float, high_fence: float) -> Severity:
    """Assign severity by how far past the fence the value sits."""
    if value is not None and value > high_fence:
        return "high"
    return "medium"


def _make_item(
    row: dict,
    exception_type: str,
    metric: str,
    value: Any,
    threshold: float,
    reason: str,
    severity: Severity,
) -> dict:
    return {
        "sale_id": int(row["sale_id"]),
        "customer_id": None if row["customer_id"] is None else int(row["customer_id"]),
        "product_id": None if row["product_id"] is None else int(row["product_id"]),
        "date": row["full_date"],
        "metric": metric,
        "value": _round(value, 4),
        "threshold": _round(threshold, 4),
        "exception_type": exception_type,
        "reason": reason,
        "severity": severity,
    }


def get_exceptions(limit: int = 50, db_engine: Engine | None = None) -> dict:
    """Return rule-based transaction exceptions plus the thresholds used.

    Two queries total: one to measure the quartiles, one to select the flagged
    transactions using those measured values as bound parameters. The 100,000
    fact rows are never transferred to Python.
    """
    bounds_rows = _execute(_BOUNDS_SQL, {}, "exception thresholds", db_engine)
    if not bounds_rows:
        raise ExceptionAnalysisError("Could not compute exception thresholds.")

    bounds_row = bounds_rows[0]
    thresholds = _build_thresholds(bounds_row)

    params = {
        "sales_upper": thresholds["sales_amount"]["upper_fence"],
        "qty_upper": thresholds["quantity"]["upper_fence"],
        "profit_upper": thresholds["profit"]["upper_fence"],
        "margin_upper": thresholds["profit_margin_pct"]["upper_fence"],
        "margin_lower": thresholds["profit_margin_pct"]["lower_fence"],
        "row_limit": int(limit),
    }
    rows = _execute(_DETECTION_SQL, params, "exception detection", db_engine)

    count_by_type = {
        "unusually_high_sales_amount": 0,
        "unusually_high_quantity": 0,
        "unusually_high_profit": 0,
        "extreme_profit_margin": 0,
        "invalid_transaction_values": 0,
    }
    if rows:
        # Window aggregates describe every flagged row, not just this page.
        count_by_type = {
            "unusually_high_sales_amount": int(rows[0]["total_high_sales"] or 0),
            "unusually_high_quantity": int(rows[0]["total_high_qty"] or 0),
            "unusually_high_profit": int(rows[0]["total_high_profit"] or 0),
            "extreme_profit_margin": int(rows[0]["total_extreme_margin"] or 0),
            "invalid_transaction_values": int(rows[0]["total_invalid"] or 0),
        }
        total_flagged = int(rows[0]["total_flagged"] or 0)
    else:
        total_flagged = 0

    sales_t = thresholds["sales_amount"]
    qty_t = thresholds["quantity"]
    profit_t = thresholds["profit"]
    margin_t = thresholds["profit_margin_pct"]

    items: list[dict] = []
    for row in rows:
        if row["high_sales"]:
            value = float(row["sales_amount"])
            items.append(
                _make_item(
                    row,
                    "unusually_high_sales_amount",
                    "sales_amount",
                    value,
                    sales_t["upper_fence"],
                    (
                        f"sales_amount {value:,.2f} is above the upper Tukey fence "
                        f"{sales_t['upper_fence']:,.2f} "
                        f"(Q3 {sales_t['q3']:,.2f} + {IQR_MULTIPLIER} x IQR {sales_t['iqr']:,.2f})."
                    ),
                    _band_severity(value, sales_t["upper_fence"], sales_t["high_fence"]),
                )
            )

        if row["high_qty"]:
            value = float(row["quantity"])
            items.append(
                _make_item(
                    row,
                    "unusually_high_quantity",
                    "quantity",
                    value,
                    qty_t["upper_fence"],
                    (
                        f"quantity {value:,.0f} is above the upper Tukey fence "
                        f"{qty_t['upper_fence']:,.2f} "
                        f"(Q3 {qty_t['q3']:,.2f} + {IQR_MULTIPLIER} x IQR {qty_t['iqr']:,.2f})."
                    ),
                    _band_severity(value, qty_t["upper_fence"], qty_t["high_fence"]),
                )
            )

        if row["high_profit"]:
            value = float(row["profit"])
            items.append(
                _make_item(
                    row,
                    "unusually_high_profit",
                    "profit",
                    value,
                    profit_t["upper_fence"],
                    (
                        f"profit {value:,.2f} is above the upper Tukey fence "
                        f"{profit_t['upper_fence']:,.2f} "
                        f"(Q3 {profit_t['q3']:,.2f} + {IQR_MULTIPLIER} x IQR {profit_t['iqr']:,.2f})."
                    ),
                    _band_severity(value, profit_t["upper_fence"], profit_t["high_fence"]),
                )
            )

        if row["extreme_margin"]:
            value = float(row["margin"])
            if value > margin_t["upper_fence"]:
                reason = (
                    f"transaction margin {value:.2f}% is above the upper Tukey fence "
                    f"{margin_t['upper_fence']:.2f}% (Q3 {margin_t['q3']:.2f}% + "
                    f"{IQR_MULTIPLIER} x IQR {margin_t['iqr']:.2f}%)."
                )
                severity = _band_severity(value, margin_t["upper_fence"], margin_t["high_fence"])
            else:
                reason = (
                    f"transaction margin {value:.2f}% is below the lower Tukey fence "
                    f"{margin_t['lower_fence']:.2f}% (Q1 {margin_t['q1']:.2f}% - "
                    f"{IQR_MULTIPLIER} x IQR {margin_t['iqr']:.2f}%)."
                )
                severity = (
                    "high"
                    if value < margin_t["lower_high_fence"]
                    else "medium"
                )
            items.append(
                _make_item(
                    row,
                    "extreme_profit_margin",
                    "profit_margin_pct",
                    value,
                    margin_t["upper_fence"] if value > margin_t["upper_fence"] else margin_t["lower_fence"],
                    reason,
                    severity,
                )
            )

        if row["is_invalid"]:
            items.append(
                _make_item(
                    row,
                    "invalid_transaction_values",
                    "transaction_validity",
                    0,
                    0,
                    (
                        "Transaction violates a data-integrity rule: "
                        f"{row['invalid_detail']}."
                    ),
                    "critical",
                )
            )

    # Present the most severe first, then a stable identifier.
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    items.sort(key=lambda item: (severity_order[item["severity"]], item["exception_type"], item["sale_id"]))

    total_exceptions = sum(count_by_type.values())

    return {
        "generated_at": datetime.now(timezone.utc),
        "method": METHOD_DESCRIPTION,
        "rules": RULES_DOCUMENTATION,
        "thresholds": thresholds,
        "count_by_type": count_by_type,
        "total_exceptions_detected": total_exceptions,
        "total_flagged_transactions": total_flagged,
        "count": len(items),
        "truncated": total_flagged > len(rows),
        "limit_applies_to": (
            "The limit caps flagged transactions returned (ordered by sale_id "
            "ascending). One transaction can raise several exceptions, so the "
            "number of items in data may exceed the limit."
        ),
        "disclaimer": (
            "Exceptions mark statistically unusual transactions for review. "
            "They are not evidence of fraud, error or misconduct."
        ),
        "data": items,
    }
