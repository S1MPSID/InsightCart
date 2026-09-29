"""Application configuration loaded from environment variables.

Credentials are never hardcoded in source. Values are read from the process
environment, with a repository-root `.env` file loaded automatically when
python-dotenv is available.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements
    load_dotenv = None


# app/config.py -> app -> scripts -> backend -> repository root
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT_ENV_FILE = REPO_ROOT / ".env"
BACKEND_ENV_FILE = BACKEND_SCRIPTS_DIR / ".env"

if load_dotenv is not None:
    # Repository root wins, so a single .env drives both the API and the loaders.
    load_dotenv(REPO_ROOT_ENV_FILE, override=False)
    load_dotenv(BACKEND_ENV_FILE, override=False)


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or unusable."""


def _redact(url: str) -> str:
    """Return a connection string safe to write to logs."""
    if "@" not in url or "//" not in url:
        return url
    scheme, _, remainder = url.partition("//")
    credentials, _, host = remainder.partition("@")
    if ":" in credentials:
        user, _, _password = credentials.partition(":")
        credentials = f"{user}:***"
    return f"{scheme}//{credentials}@{host}"


def get_database_url() -> str:
    """Return the PostgreSQL connection string from the environment."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ConfigurationError(
            "DATABASE_URL is not set. Copy .env.example to .env in the "
            "repository root and set a valid PostgreSQL connection string."
        )
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise ConfigurationError(
            "DATABASE_URL must start with 'postgresql://' or 'postgres://'."
        )
    return database_url


def get_safe_database_url() -> str:
    """Return the connection string with the password masked, for logging."""
    try:
        return _redact(get_database_url())
    except ConfigurationError:
        return "<DATABASE_URL not set>"


def get_cors_origins() -> list[str]:
    """Return the allowed CORS origins."""
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def get_log_level() -> str:
    """Return the configured log level name."""
    return os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
