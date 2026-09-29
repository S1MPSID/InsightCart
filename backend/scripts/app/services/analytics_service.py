"""Analytics queries backed by the PostgreSQL `retail` star schema.

Every figure is aggregated in SQL. The raw 100,000 fact rows are never pulled
into Python, and no metric is hardcoded.

Schema used
-----------
    retail.fact_sales     sale_id, customer_id, product_id, date_id,
                          quantity, sales_amount, profit
    retail.dim_date       date_id, full_date, day, month, quarter, year, day_name
    retail.dim_products   product_id, product_name, category, brand,
                          cost_price, selling_price
    retail.dim_customers  customer_id, customer_name, gender, age, city, state,
                          join_date

Column mapping for retail.fact_sales:
    orders       -> COUNT(*)
    quantity     -> SUM(quantity)
    revenue      -> SUM(sales_amount)
    profit       -> SUM(profit)
    margin_pct   -> SUM(profit) / SUM(sales_amount) * 100
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

logger = logging.getLogger(__name__)

# Identifiers are module constants only; none of these come from user input.
FACT_TABLE = "retail.fact_sales"
DATE_DIM = "retail.dim_date"
PRODUCT_DIM = "retail.dim_products"
CUSTOMER_DIM = "retail.dim_customers"

# Margin is reported to 4 decimal places (37.5653 for the reference dataset).
MARGIN_PRECISION = 4
# Monetary values are reported to 2 decimal places.
MONEY_PRECISION = 2

# Whitelists. A user-supplied sort key is only ever used as a dictionary lookup
# into these maps, so arbitrary SQL fragments can never reach the query text.
GRANULARITIES: tuple[str, ...] = ("day", "week", "month", "quarter", "year")
PRODUCT_SORT_COLUMNS: dict[str, str] = {
    "revenue": "SUM(f.sales_amount)",
    "profit": "SUM(f.profit)",
    "quantity": "SUM(f.quantity)",
    "orders": "COUNT(*)",
}
CUSTOMER_SORT_COLUMNS: dict[str, str] = {
    "revenue": "SUM(f.sales_amount)",
    "profit": "SUM(f.profit)",
    "orders": "COUNT(*)",
    "quantity": "SUM(f.quantity)",
}

# Fact-to-dimension joins are static, so every endpoint needs exactly one query.
FACT_JOIN_DATE = f"FROM {FACT_TABLE} f JOIN {DATE_DIM} d ON d.date_id = f.date_id"
FACT_JOIN_PRODUCT = f"FROM {FACT_TABLE} f JOIN {PRODUCT_DIM} p ON p.product_id = f.product_id"
FACT_JOIN_CUSTOMER = f"FROM {FACT_TABLE} f JOIN {CUSTOMER_DIM} c ON c.customer_id = f.customer_id"

# Column list shared by the grouped endpoints.
GROUPED_MEASURES = """
    COALESCE(SUM(f.sales_amount), 0)    AS revenue,
    COALESCE(SUM(f.profit), 0)          AS profit,
    COUNT(*)                            AS orders,
    COALESCE(SUM(f.quantity), 0)        AS units
"""


class AnalyticsError(RuntimeError):
    """Raised when an analytics query cannot be completed."""


class InvalidSortKey(ValueError):
    """Raised when a sort key is not in the whitelist."""


def _round_metric(value: Any) -> float:
    """Convert a SQL numeric/Decimal to a JSON-safe float at 2 decimals."""
    if value is None:
        return 0.0
    return round(float(Decimal(value)), MONEY_PRECISION)


def _calculate_margin(revenue: float, profit: float) -> float:
    """Return profit as a percentage of revenue, or 0.0 when revenue is zero."""
    if revenue == 0:
        return 0.0
    return round((profit / revenue) * 100, MARGIN_PRECISION)


def _average_order_value(revenue: float, orders: int) -> float:
    """Return revenue per transaction, or 0.0 when there are no orders."""
    if orders == 0:
        return 0.0
    return round(revenue / orders, MONEY_PRECISION)


def _execute(sql: str, params: dict[str, Any], label: str, db_engine: Engine | None) -> list[dict]:
    """Run one aggregation and return list-of-dict rows.

    Any database failure is logged with full detail server-side and re-raised as
    AnalyticsError so routes can return a sanitised response.
    """
    active_engine = db_engine or engine
    try:
        with active_engine.connect() as connection:
            result = connection.execute(text(sql), params)
            return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        logger.exception("%s query failed: %s", label, exc)
        raise AnalyticsError(f"Failed to load {label} from PostgreSQL.") from exc


def get_dashboard_summary(db_engine: Engine | None = None) -> dict:
    """Return the executive KPI set in a single aggregated round-trip.

    Uses the real fact columns: sales_amount, profit, quantity. Previously this
    query referenced sale_price/cost_price, which do not exist on
    retail.fact_sales, and the endpoint failed with HTTP 500.
    """
    # One pass over the fact table instead of a separate query per KPI.
    rows = _execute(
        f"""
        SELECT
            COUNT(*)                          AS orders,
            COALESCE(SUM(f.quantity), 0)      AS units,
            COALESCE(SUM(f.sales_amount), 0)  AS revenue,
            COALESCE(SUM(f.profit), 0)        AS profit
        FROM {FACT_TABLE} f
        """,
        {},
        "dashboard summary",
        db_engine,
    )
    row = rows[0]

    orders = int(row["orders"] or 0)
    units = int(row["units"] or 0)
    revenue = float(row["revenue"] or 0)
    profit = float(row["profit"] or 0)

    return {
        "revenue": _round_metric(revenue),
        "profit": _round_metric(profit),
        "orders": orders,
        "quantity": units,
        "margin": _calculate_margin(revenue, profit),
        "average_order_value": _average_order_value(revenue, orders),
    }


def get_trends(
    granularity: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 1461,
    db_engine: Engine | None = None,
) -> dict:
    """Return revenue/profit/orders/units grouped by real calendar period.

    Periods come from retail.dim_date.full_date, so results are actual calendar
    dates rather than the opaque date_id surrogate key. Filtering and grouping
    happen in the database; only aggregated periods are returned to the client.
    """
    if granularity not in GRANULARITIES:
        raise InvalidSortKey(f"Unsupported granularity: {granularity!r}")

    conditions: list[str] = []
    params: dict[str, Any] = {"granularity": granularity, "row_limit": int(limit) + 1}
    # Optional filters are added as fixed fragments; the values stay bound.
    if start_date is not None:
        conditions.append("d.full_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("d.full_date <= :end_date")
        params["end_date"] = end_date
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Fetch one extra row to detect truncation without a second COUNT query.
    rows = _execute(
        f"""
        SELECT
            CAST(date_trunc(:granularity, d.full_date) AS date) AS period,
            {GROUPED_MEASURES}
        {FACT_JOIN_DATE}
        {where_clause}
        GROUP BY 1
        ORDER BY 1 ASC
        LIMIT :row_limit
        """,
        params,
        f"{granularity} trend",
        db_engine,
    )

    truncated = len(rows) > limit
    rows = rows[:limit]

    data = []
    for row in rows:
        revenue = float(row["revenue"] or 0)
        profit = float(row["profit"] or 0)
        data.append(
            {
                "period": row["period"],
                "revenue": _round_metric(revenue),
                "profit": _round_metric(profit),
                "orders": int(row["orders"] or 0),
                "quantity": int(row["units"] or 0),
                "margin": _calculate_margin(revenue, profit),
            }
        )

    return {
        "granularity": granularity,
        "start_date": start_date,
        "end_date": end_date,
        "count": len(data),
        "truncated": truncated,
        "data": data,
    }


def get_category_analytics(limit: int = 100, db_engine: Engine | None = None) -> dict:
    """Return revenue/profit/orders/units grouped by product category.

    Category lives on retail.dim_products, so this is a real dimension
    attribute rather than anything inferred from the fact table.
    """
    rows = _execute(
        f"""
        SELECT
            p.category,
            {GROUPED_MEASURES}
        {FACT_JOIN_PRODUCT}
        GROUP BY 1
        ORDER BY SUM(f.sales_amount) DESC, 1 ASC
        LIMIT :row_limit
        """,
        {"row_limit": int(limit) + 1},
        "category analytics",
        db_engine,
    )

    truncated = len(rows) > limit
    rows = rows[:limit]

    data = []
    for row in rows:
        revenue = float(row["revenue"] or 0)
        profit = float(row["profit"] or 0)
        orders = int(row["orders"] or 0)
        data.append(
            {
                "category": row["category"],
                "revenue": _round_metric(revenue),
                "profit": _round_metric(profit),
                "orders": orders,
                "quantity": int(row["units"] or 0),
                "margin": _calculate_margin(revenue, profit),
                "average_order_value": _average_order_value(revenue, orders),
            }
        )

    return {"count": len(data), "truncated": truncated, "data": data}


def get_product_analytics(
    sort_by: str = "revenue",
    limit: int = 20,
    category: str | None = None,
    db_engine: Engine | None = None,
) -> dict:
    """Return top products with their name and category from the product dimension."""
    if sort_by not in PRODUCT_SORT_COLUMNS:
        raise InvalidSortKey(f"Unsupported sort_by: {sort_by!r}")

    sort_expression = PRODUCT_SORT_COLUMNS[sort_by]
    conditions: list[str] = []
    params: dict[str, Any] = {"row_limit": int(limit) + 1}
    if category is not None:
        conditions.append("p.category = :category")
        params["category"] = category
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Sort key is whitelisted; product_id breaks ties for stable pagination.
    rows = _execute(
        f"""
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.brand,
            {GROUPED_MEASURES}
        {FACT_JOIN_PRODUCT}
        {where_clause}
        GROUP BY 1, 2, 3, 4
        ORDER BY {sort_expression} DESC, p.product_id ASC
        LIMIT :row_limit
        """,
        params,
        "product analytics",
        db_engine,
    )

    truncated = len(rows) > limit
    rows = rows[:limit]

    data = []
    for row in rows:
        revenue = float(row["revenue"] or 0)
        profit = float(row["profit"] or 0)
        orders = int(row["orders"] or 0)
        data.append(
            {
                "product_id": int(row["product_id"]),
                "product_name": row["product_name"],
                "category": row["category"],
                "brand": row["brand"],
                "revenue": _round_metric(revenue),
                "profit": _round_metric(profit),
                "orders": orders,
                "quantity": int(row["units"] or 0),
                "margin": _calculate_margin(revenue, profit),
            }
        )

    return {"sort_by": sort_by, "count": len(data), "truncated": truncated, "data": data}


def get_customer_analytics(
    sort_by: str = "revenue",
    limit: int = 20,
    db_engine: Engine | None = None,
) -> dict:
    """Return top customers with their name and state from the customer dimension."""
    if sort_by not in CUSTOMER_SORT_COLUMNS:
        raise InvalidSortKey(f"Unsupported sort_by: {sort_by!r}")

    sort_expression = CUSTOMER_SORT_COLUMNS[sort_by]
    rows = _execute(
        f"""
        SELECT
            c.customer_id,
            c.customer_name,
            c.state,
            {GROUPED_MEASURES}
        {FACT_JOIN_CUSTOMER}
        GROUP BY 1, 2, 3
        ORDER BY {sort_expression} DESC, c.customer_id ASC
        LIMIT :row_limit
        """,
        {"row_limit": int(limit) + 1},
        "customer analytics",
        db_engine,
    )

    truncated = len(rows) > limit
    rows = rows[:limit]

    data = []
    for row in rows:
        revenue = float(row["revenue"] or 0)
        profit = float(row["profit"] or 0)
        orders = int(row["orders"] or 0)
        data.append(
            {
                "customer_id": int(row["customer_id"]),
                "customer_name": row["customer_name"],
                "state": row["state"],
                "revenue": _round_metric(revenue),
                "profit": _round_metric(profit),
                "orders": orders,
                "quantity": int(row["units"] or 0),
                "margin": _calculate_margin(revenue, profit),
                "average_order_value": _average_order_value(revenue, orders),
            }
        )

    return {"sort_by": sort_by, "count": len(data), "truncated": truncated, "data": data}
