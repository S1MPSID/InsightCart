"""FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import ConfigurationError, get_cors_origins, get_log_level
from app.routes.analytics import router as analytics_router
from app.routes.data_quality import router as data_quality_router
from app.routes.exceptions import router as exceptions_router

logging.basicConfig(
    level=get_log_level(),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InsightCart Analytics API",
    description=(
        "Retail analytics API. All metrics are aggregated in SQL against "
        "PostgreSQL and calculated dynamically."
    ),
    version="1.0.0",
)

# Origins are configurable; credentials are never combined with a wildcard.
_cors_origins = get_cors_origins()
_allow_all = "*" in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _allow_all,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(analytics_router, prefix="/api")
app.include_router(data_quality_router, prefix="/api")
app.include_router(exceptions_router, prefix="/api")


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Database failures return a clean 503 without leaking SQL or credentials."""
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database is unavailable or rejected the request.",
            "error_code": "DATABASE_UNAVAILABLE",
        },
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    logger.error("Server configuration problem: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Server is misconfigured. Check the environment settings.",
            "error_code": "SERVER_MISCONFIGURED",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Request validation failed on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request parameters are invalid.",
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the traceback server-side, return a generic message."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal error occurred.",
            "error_code": "INTERNAL_ERROR",
        },
    )
