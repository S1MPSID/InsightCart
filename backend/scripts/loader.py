"""Reusable, idempotent CSV -> PostgreSQL loading helpers.

Design goals
------------
1. Re-running a loader must never duplicate records.
2. Re-running a loader must never silently destroy data.
3. The dimension CSVs contain no id column, so the surrogate key is derived
   positionally (row 1 -> id 1) to match the existing `retail` schema.
4. Paths are resolved relative to this file, not the current working directory.

Default behaviour (verify) is read-only: if the target table already holds the
expected number of rows and the aggregate checksum matches, the loader reports
"already loaded" and exits without writing anything. Use --force to reload.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_database_url, get_safe_database_url
from app.database import engine as default_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger("insightcart.loader")

RETAIL_SCHEMA = "retail"

# Numeric columns used to fingerprint a table for the "already loaded" check.
_CHECKSUM_EXPR = {
    "quantity": "COALESCE(SUM(quantity), 0)",
    "sales_amount": "COALESCE(SUM(sales_amount), 0)",
    "profit": "COALESCE(SUM(profit), 0)",
    "cost_price": "COALESCE(SUM(cost_price), 0)",
    "selling_price": "COALESCE(SUM(selling_price), 0)",
}

# Relative float tolerance for comparing a Pandas fingerprint with PostgreSQL.
CHECKSUM_TOLERANCE = 0.01


def build_engine() -> Engine:
    """Return the application engine, validating configuration first."""
    get_database_url()
    logger.info("Target database: %s", get_safe_database_url())
    return default_engine


def _table_exists(db: Engine, table: str) -> bool:
    with db.connect() as conn:
        return bool(
            conn.execute(
                text("SELECT to_regclass(:qualified) IS NOT NULL"),
                {"qualified": f"{RETAIL_SCHEMA}.{table}"},
            ).scalar()
        )


def _columns(db: Engine, table: str) -> list[str]:
    with db.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
                """
            ),
            {"schema": RETAIL_SCHEMA, "table": table},
        ).fetchall()
    return [r[0] for r in rows]


def _fingerprint(db: Engine, table: str) -> dict:
    """Return row count and per-column sums for a table."""
    available = set(_columns(db, table))
    parts = ["COUNT(*) AS row_count"]
    params: dict[str, object] = {}
    for index, (column, expr) in enumerate(_CHECKSUM_EXPR.items()):
        if column not in available:
            continue
        key = f"sum_{index}"
        parts.append(f"{expr} AS {key}")
        params[key] = column

    sql = f"SELECT {', '.join(parts)} FROM {RETAIL_SCHEMA}.{table}"
    with db.connect() as conn:
        row = conn.execute(text(sql), params).mappings().one()
    return dict(row)


def _csv_fingerprint(frame: pd.DataFrame) -> dict:
    result: dict[str, object] = {"row_count": int(len(frame))}
    for index, column in enumerate(_CHECKSUM_EXPR):
        if column in frame.columns:
            result[f"sum_{index}"] = float(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())
    return result


def _fingerprints_match(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value is None:
            problems.append(f"{key}: missing in database")
            continue
        if isinstance(expected_value, float):
            tolerance = max(CHECKSUM_TOLERANCE, abs(expected_value) * 1e-9)
            if abs(float(actual_value) - expected_value) > tolerance:
                problems.append(
                    f"{key}: csv={expected_value:.2f} db={float(actual_value):.2f}"
                )
        elif int(actual_value) != int(expected_value):
            problems.append(f"{key}: csv={expected_value} db={actual_value}")
    return (not problems), problems


def _truncate(db: Engine, table: str) -> None:
    with db.begin() as conn:
        try:
            conn.execute(text(f"TRUNCATE TABLE {RETAIL_SCHEMA}.{table}"))
        except SQLAlchemyError:
            # Referencing tables may block TRUNCATE; fall back to row deletes.
            logger.warning("TRUNCATE failed for %s, falling back to DELETE", table)
            conn.execute(text(f"DELETE FROM {RETAIL_SCHEMA}.{table}"))


def _reset_sequence(db: Engine, table: str, id_column: str) -> None:
    """Keep any serial/identity sequence aligned after an explicit id insert."""
    with db.connect() as conn:
        sequence = conn.execute(
            text("SELECT pg_get_serial_sequence(:qualified, :column)"),
            {"qualified": f"{RETAIL_SCHEMA}.{table}", "column": id_column},
        ).scalar()
        if not sequence:
            return
        max_id = conn.execute(
            text(f"SELECT COALESCE(MAX({id_column}), 1) FROM {RETAIL_SCHEMA}.{table}")
        ).scalar()
    with db.begin() as conn:
        conn.execute(
            text("SELECT setval(:seq, :value, true)"),
            {"seq": sequence, "value": int(max_id)},
        )
    logger.info("Reset sequence %s to %s", sequence, max_id)


def load_csv(
    csv_path: Path,
    table: str,
    id_column: str,
    force: bool = False,
    db: Engine | None = None,
) -> int:
    """Load one CSV into `retail.<table>` without ever duplicating rows.

    Returns a process exit code (0 on success, 1 on failure).
    """
    db = db or build_engine()

    if not csv_path.exists():
        logger.error("CSV not found: %s", csv_path)
        return 1

    frame = pd.read_csv(csv_path)
    logger.info("%s -> retail.%s (%d rows)", csv_path.name, table, len(frame))

    if not _table_exists(db, table):
        logger.info("Table retail.%s does not exist yet; creating it", table)
        force = True

    expected = _csv_fingerprint(frame)
    actual = _fingerprint(db, table) if not force else {}
    matches, problems = _fingerprints_match(expected, actual)

    if matches and not force:
        logger.info(
            "retail.%s already matches %s (row_count=%s). Nothing to do.",
            table,
            csv_path.name,
            actual.get("row_count"),
        )
        return 0

    if not force and not matches:
        logger.error(
            "retail.%s does not match %s and --force was not supplied. "
            "Refusing to append, which would duplicate records. Problems: %s",
            table,
            csv_path.name,
            "; ".join(problems) or "unknown",
        )
        return 1

    if force:
        if _table_exists(db, table):
            logger.info("Reloading retail.%s (truncate + insert)", table)
            _truncate(db, table)
        else:
            logger.info("Creating retail.%s", table)

        # The CSVs have no id column, so derive it positionally: row 1 -> id 1.
        payload = frame.copy()
        if id_column not in payload.columns:
            payload.insert(0, id_column, range(1, len(payload) + 1))
        else:
            payload[id_column] = range(1, len(payload) + 1)

        target_columns = set(_columns(db, table))
        if target_columns:
            unknown = [c for c in payload.columns if c not in target_columns]
            if unknown:
                logger.error(
                    "CSV columns not present in retail.%s: %s", table, ", ".join(unknown)
                )
                return 1

        payload.to_sql(
            table,
            db,
            schema=RETAIL_SCHEMA,
            if_exists="append",
            index=False,
        )
        if _table_exists(db, table):
            _reset_sequence(db, table, id_column)

    final = _fingerprint(db, table)
    verified, final_problems = _fingerprints_match(expected, final)
    if not verified:
        logger.error("Post-load verification FAILED for retail.%s: %s", table, "; ".join(final_problems))
        return 1

    logger.info("retail.%s verified: row_count=%s", table, final.get("row_count"))
    return 0


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--force",
        action="store_true",
        help="truncate and reload the target table instead of verifying",
    )
    return parser


def run(targets: Iterable[tuple[str, str, str]], force: bool) -> int:
    """Load a sequence of (csv_name, table, id_column) targets in order."""
    base = Path(__file__).resolve().parent
    db = build_engine()
    for csv_name, table, id_column in targets:
        code = load_csv(base / csv_name, table, id_column, force=force, db=db)
        if code != 0:
            logger.error("Aborting: retail.%s failed to load", table)
            return code
    return 0
