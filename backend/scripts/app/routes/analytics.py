"""Read-only analytics API routes.

Every endpoint runs a single SQL aggregation and returns a typed JSON payload.
No endpoint accepts free-form SQL, and every numeric value is computed in the
database rather than in Python.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services import analytics_service as svc
from app.services.analytics_service import AnalyticsError, InvalidSortKey

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])

Granularity = Literal["day", "week", "month", "quarter", "year"]
ProductSort = Literal["revenue", "profit", "quantity", "orders"]
CustomerSort = Literal["revenue", "profit", "orders", "quantity"]

UNAVAILABLE = "Analytics data is temporarily unavailable. Please retry shortly."


# --------------------------------------------------------------------------
# Response models
# --------------------------------------------------------------------------


class DashboardSummary(BaseModel):
    """Executive KPI payload. All values are computed in SQL, never hardcoded."""

    revenue: float = Field(..., description="Total revenue from SUM(sales_amount)")
    profit: float = Field(..., description="Total profit from SUM(profit)")
    orders: int = Field(..., description="Transaction count")
    quantity: int = Field(..., description="Total units sold")
    margin: float = Field(..., description="Profit as a percentage of revenue")
    average_order_value: float = Field(..., description="Revenue divided by orders")


class TrendPoint(BaseModel):
    """One aggregated calendar period from retail.dim_date."""

    period: date = Field(..., description="Truncated calendar date for the period")
    revenue: float
    profit: float
    orders: int
    quantity: int
    margin: float


class TrendResponse(BaseModel):
    granularity: Granularity
    start_date: date | None = None
    end_date: date | None = None
    count: int = Field(..., description="Number of periods returned")
    truncated: bool = Field(
        ..., description="True when more periods exist than the requested limit"
    )
    data: list[TrendPoint]


class CategoryRow(BaseModel):
    category: str
    revenue: float
    profit: float
    orders: int
    quantity: int
    margin: float
    average_order_value: float


class CategoryResponse(BaseModel):
    count: int
    truncated: bool
    data: list[CategoryRow]


class ProductRow(BaseModel):
    product_id: int
    product_name: str
    category: str
    brand: str
    revenue: float
    profit: float
    orders: int
    quantity: int
    margin: float


class ProductResponse(BaseModel):
    sort_by: ProductSort
    count: int
    truncated: bool
    data: list[ProductRow]


class CustomerRow(BaseModel):
    customer_id: int
    customer_name: str
    state: str
    revenue: float
    profit: float
    orders: int
    quantity: int
    margin: float
    average_order_value: float


class CustomerResponse(BaseModel):
    sort_by: CustomerSort
    count: int
    truncated: bool
    data: list[CustomerRow]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date.",
        )


def _run(callable_, label: str):
    """Execute a service call, mapping expected errors to HTTP responses."""
    try:
        return callable_()
    except InvalidSortKey as exc:
        logger.warning("Rejected %s request: %s", label, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported sort key.",
        ) from exc
    except AnalyticsError as exc:
        logger.warning("%s unavailable: %s", label, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE,
        ) from exc


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.get(
    "/dashboard-summary",
    response_model=DashboardSummary,
    summary="Executive KPI summary",
)
def dashboard_summary() -> DashboardSummary:
    result = _run(svc.get_dashboard_summary, "dashboard summary")
    logger.info("Dashboard summary served: %s orders", result["orders"])
    return DashboardSummary(**result)


@router.get(
    "/trends",
    response_model=TrendResponse,
    summary="Revenue, profit, orders and units per calendar period",
)
def trends(
    granularity: Granularity = Query(
        default="day",
        description="Period size applied to dim_date.full_date in SQL.",
    ),
    start_date: date | None = Query(default=None, description="Inclusive lower bound (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="Inclusive upper bound (YYYY-MM-DD)"),
    limit: int = Query(
        default=1461,
        ge=1,
        le=2000,
        description="Maximum periods to return. 1461 covers the full date dimension.",
    ),
) -> TrendResponse:
    _validate_date_range(start_date, end_date)
    result = _run(
        lambda: svc.get_trends(
            granularity=granularity,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        ),
        "trends",
    )
    return TrendResponse(**result)


@router.get(
    "/categories",
    response_model=CategoryResponse,
    summary="Revenue, profit, orders and units by product category",
)
def categories(
    limit: int = Query(default=100, ge=1, le=1000),
) -> CategoryResponse:
    result = _run(lambda: svc.get_category_analytics(limit=limit), "categories")
    return CategoryResponse(**result)


@router.get(
    "/products",
    response_model=ProductResponse,
    summary="Top products with product name and category",
)
def products(
    sort_by: ProductSort = Query(default="revenue", description="Metric to rank by"),
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None, max_length=100),
) -> ProductResponse:
    result = _run(
        lambda: svc.get_product_analytics(sort_by=sort_by, limit=limit, category=category),
        "products",
    )
    return ProductResponse(**result)


@router.get(
    "/customers",
    response_model=CustomerResponse,
    summary="Top customers with customer name and state",
)
def customers(
    sort_by: CustomerSort = Query(default="revenue", description="Metric to rank by"),
    limit: int = Query(default=20, ge=1, le=100),
) -> CustomerResponse:
    result = _run(
        lambda: svc.get_customer_analytics(sort_by=sort_by, limit=limit),
        "customers",
    )
    return CustomerResponse(**result)
