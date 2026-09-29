"""SQLAlchemy engine construction.

The connection string comes from the `DATABASE_URL` environment variable
(see app/config.py). No credentials live in this file.
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_database_url, get_safe_database_url

logger = logging.getLogger(__name__)


def _build_engine() -> Engine:
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    # Log only the redacted form so the password never reaches the log file.
    logger.info("Database engine created for %s", get_safe_database_url())
    return engine


engine: Engine = _build_engine()
