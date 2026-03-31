"""
Data ingestion module.

Provides a simple utility to read a CSV file and store its contents in a
PostgreSQL (or any SQLAlchemy‑compatible) database.

The implementation is deliberately lightweight:
* Column types are inferred as generic ``String`` columns.  This keeps the
  module usable without complex type‑mapping logic.
* If the target table already exists, it is dropped and recreated to match the
  CSV header.  This mirrors typical “load‑once” ingestion workflows.
* The database URL is taken from the ``DATABASE_URL`` environment variable.
  If not set, a temporary SQLite database is used – this makes the module
  runnable in test environments without a real PostgreSQL instance.

Example
-------
>>> from app.ingestion import ingest_csv
>>> ingest_csv("data/users.csv", "users")
"""

import csv
import os
from pathlib import Path
from typing import List, Sequence

from sqlalchemy import MetaData, Table, Column, String, create_engine, insert, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def _get_engine(database_url: str | None = None) -> Engine:
    """
    Create a SQLAlchemy engine.

    Parameters
    ----------
    database_url: str | None
        The database connection URL. If ``None`` the function reads the
        ``DATABASE_URL`` environment variable.  When that variable is also not
        defined, an in‑memory SQLite engine is returned – this is safe for unit
        tests and local experimentation.

    Returns
    -------
    Engine
        A SQLAlchemy engine instance.
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    return create_engine(database_url, future=True)


def _infer_columns(header: Sequence[str])