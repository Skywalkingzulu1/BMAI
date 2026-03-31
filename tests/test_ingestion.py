import os
import tempfile
import csv
from pathlib import Path

import pytest
from sqlalchemy import select, inspect, text
from sqlalchemy.engine import Engine

from app.ingestion import ingest_csv, _infer_columns, _get_engine


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with a known schema and data."""
    with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False, suffix=".csv") as tmp:
        writer = csv.writer(tmp)
        # Header includes spaces and a leading digit to test sanitisation.
        writer.writerow(["id", "first name", "2nd_address"])
        writer.writerow(["1", "Alice", "123 Main St"])
        writer.writerow(["2", "Bob", "456 Oak Ave"])
        tmp_path = Path(tmp.name)
    yield tmp_path
    tmp_path.unlink(missing_ok=True)


@pytest.fixture
def sqlite_engine():
    """Provide a fresh in‑memory SQLite engine for each test."""
    engine = _get_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


def test_infer_columns_sanitises_names():
    header = ["id", "first name", "2nd_address", "email@domain.com"]
    columns = _infer_columns(header)
    names = [col.name for col in columns]
    assert names == ["id", "first_name", "col_2nd_address", "email_domain_com"]


def test_ingest_csv_creates_table_and_inserts_rows(temp_csv_file, sqlite_engine):
    # Ingest the CSV into a table called 'users'
    ingest_csv(temp_csv_file, "users", database_url="sqlite:///:memory:")

    # Verify that the table exists and has the expected columns.
    inspector = inspect(sqlite_engine)
    assert "users" in inspector.get_table_names()

    columns_info = inspector.get_columns("users")
    column_names = [col["name"] for col in columns_info]
    # Expected sanitized column names.
    assert set(column_names) == {"id", "first_name", "col_2nd_address"}

    # Verify row count and content.
    with sqlite_engine.connect() as conn:
        result = conn.execute(select(text("*")).select_from(text("users")))
        rows = result.fetchall()
        assert len(rows) == 2
        # Convert Row objects to dicts for easier assertion.
        row_dicts = [dict(row) for row in rows]
        assert {"id": "1", "first_name": "Alice", "col_2nd_address": "123 Main St"} in row_dicts
        assert {"id": "2", "first_name": "Bob", "col_2nd_address": "456 Oak Ave"} in row_dicts


def test_ingest_csv_replaces_existing_table(temp_csv_file, sqlite_engine):
    # First ingestion.
    ingest_csv(temp_csv_file, "employees", database_url="sqlite:///:memory:")
    # Second ingestion with a different CSV (same schema, different data).
    # Create a second CSV file.
    second_csv = tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False, suffix=".csv")
    writer = csv.writer(second_csv)
    writer.writerow(["id", "first name"])
    writer.writerow(["10", "Charlie"])
    second_csv_path = Path(second_csv.name)
    second_csv.close()

    try:
        ingest_csv(second_csv_path, "employees", database_url="sqlite:///:memory:")
        # Verify that only the new row exists.
        with sqlite_engine.connect() as conn:
            result = conn.execute(select(text("*")).select_from(text("employees")))
            rows = result.fetchall()
            assert len(rows) == 1
            row = dict(rows[0])
            assert row["id"] == "10"
            assert row["first_name"] == "Charlie"
    finally:
        second_csv_path.unlink(missing_ok=True)