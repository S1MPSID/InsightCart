"""Data quality and reconciliation API routes."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services import data_quality_service as svc
from app.services.analytics_service import AnalyticsError
from app.services.data_quality_service import SourceFileMissing

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data-quality"])

CheckStatus = Literal["PASS", "FAIL", "INFO"]
ReconciliationStatus = Literal["PASS", "FAIL"]


class DataQualityCheck(BaseModel):
    """A single validation rule evaluated against retail.fact_sales."""

    name: str = Field(..., description="Stable identifier for the check")
    description: str = Field(..., description="What the check measures")
    value: int = Field(..., description="Observed value the check evaluated")
    status: CheckStatus
    explanation: str = Field(..., description="Why this status was assigned")
    details: dict = Field(default_factory=dict, description="Supporting values")


class DataQualityResponse(BaseModel):
    generated_at: datetime
    table: str
    total_checks: int
    passed: int
    failed: int
    informational: int
    overall_status: CheckStatus = Field(
        ..., description="FAIL if any check failed, otherwise PASS"
    )
    checks: list[DataQualityCheck]


class ReconciliationMetric(BaseModel):
    """One metric compared between the CSV source and PostgreSQL."""

    metric: str
    source_value: float = Field(..., description="Value computed in Pandas from the CSV")
    database_value: float = Field(..., description="Value aggregated in PostgreSQL")
    difference: float = Field(..., description="source_value - database_value")
    tolerance: float = Field(..., description="Allowed absolute difference")
    status: ReconciliationStatus
    note: str = Field(..., description="Comparison rule and observed difference")


class ReconciliationResponse(BaseModel):
    generated_at: datetime
    source: str
    database: str
    source_file: str
    tolerance_policy: str
    total_metrics: int
    passed: int
    failed: int
    overall_status: ReconciliationStatus
    metrics: list[ReconciliationMetric]


@router.get(
    "/data-quality",
    response_model=DataQualityResponse,
    summary="Data quality validation checks on retail.fact_sales",
)
def data_quality() -> DataQualityResponse:
    try:
        result = svc.get_data_quality_report()
    except AnalyticsError as exc:
        logger.warning("Data quality report unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data quality checks are temporarily unavailable. Please retry shortly.",
        ) from exc

    logger.info(
        "Data quality served: %s checks, %s failed, overall %s",
        result["total_checks"],
        result["failed"],
        result["overall_status"],
    )
    return DataQualityResponse(**result)


@router.get(
    "/reconciliation",
    response_model=ReconciliationResponse,
    summary="Compare Pandas CSV totals against PostgreSQL totals",
)
def reconciliation() -> ReconciliationResponse:
    try:
        result = svc.get_reconciliation_report()
    except SourceFileMissing as exc:
        logger.error("Reconciliation source unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconciliation source file is unavailable.",
        ) from exc
    except AnalyticsError as exc:
        logger.warning("Reconciliation unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconciliation is temporarily unavailable. Please retry shortly.",
        ) from exc

    logger.info(
        "Reconciliation served: %s metrics, %s failed, overall %s",
        result["total_metrics"],
        result["failed"],
        result["overall_status"],
    )
    return ReconciliationResponse(**result)
