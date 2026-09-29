"""Exception analysis API route."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services import exception_service as svc
from app.services.analytics_service import AnalyticsError
from app.services.exception_service import ExceptionAnalysisError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exceptions"])

Severity = Literal["critical", "high", "medium"]


class ThresholdBand(BaseModel):
    """Measured quartiles and the derived fences for one metric."""

    q1: float | None = None
    q3: float | None = None
    iqr: float | None = None
    upper_fence: float | None = None
    high_fence: float | None = None
    lower_fence: float | None = None
    lower_high_fence: float | None = None


class Thresholds(BaseModel):
    sales_amount: ThresholdBand
    quantity: ThresholdBand
    profit: ThresholdBand
    profit_margin_pct: ThresholdBand


class RuleDocumentation(BaseModel):
    rule_id: str
    description: str
    severity: str


class ExceptionItem(BaseModel):
    """A single flagged transaction. One row per rule that fired."""

    sale_id: int
    customer_id: int | None = None
    product_id: int | None = None
    # Aliased so the JSON key stays "date" without shadowing the date type.
    transaction_date: date | None = Field(
        None,
        alias="date",
        description="Calendar date resolved from retail.dim_date",
    )
    metric: str = Field(..., description="Column or measure the rule evaluated")
    value: float | None = Field(None, description="Observed value for the metric")
    threshold: float | None = Field(None, description="Fence the value was compared against")
    exception_type: str
    reason: str = Field(..., description="Why this row was flagged, with the actual numbers")
    severity: Severity


class ExceptionResponse(BaseModel):
    generated_at: datetime
    method: str = Field(..., description="Statistical method used to derive thresholds")
    rules: list[RuleDocumentation]
    thresholds: Thresholds
    count_by_type: dict[str, int]
    total_exceptions_detected: int = Field(
        ..., description="Exception instances across the whole dataset"
    )
    total_flagged_transactions: int
    count: int = Field(..., description="Exception instances returned in this response")
    truncated: bool
    limit_applies_to: str = Field(
        ..., description="Clarifies what the limit parameter caps"
    )
    disclaimer: str
    data: list[ExceptionItem]


@router.get(
    "/exceptions",
    response_model=ExceptionResponse,
    summary="Rule-based transaction exceptions using Tukey IQR thresholds",
)
def exceptions(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum flagged transactions to return. Each transaction may raise several exceptions.",
    ),
) -> ExceptionResponse:
    try:
        result = svc.get_exceptions(limit=limit)
    except (ExceptionAnalysisError, AnalyticsError) as exc:
        logger.warning("Exception analysis unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exception analysis is temporarily unavailable. Please retry shortly.",
        ) from exc

    logger.info(
        "Exceptions served: %s instances across %s flagged transactions",
        result["total_exceptions_detected"],
        result["total_flagged_transactions"],
    )
    return ExceptionResponse(**result)
