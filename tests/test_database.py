"""Tests for database module."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile

from src.load.database import DatabaseManager
from src.extract.loader import load_raw_data
from src.transform.cleaner import clean_data
from src.transform.enricher import calculate_coverage_gap, add_derived_metrics


@pytest.fixture
def enriched_data():
    """Get enriched data for testing."""
    raw = load_raw_data()
    clean = clean_data(raw)
    enriched = calculate_coverage_gap(clean)
    return add_derived_metrics(enriched)


@pytest.fixture
def temp_db():
    """Create a temporary database path for testing."""
    # Create a temp directory and generate a path (don't create the file)
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.duckdb"

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()
    Path(temp_dir).rmdir()


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_connect_and_close(self, temp_db):
        """Should connect and close without error."""
        db = DatabaseManager(temp_db)
        db.connect()
        assert db.conn is not None
        db.close()
        assert db.conn is None

    def test_context_manager(self, temp_db):
        """Should work as context manager."""
        with DatabaseManager(temp_db) as db:
            assert db.conn is not None
        # Connection should be closed after context

    def test_create_schema(self, temp_db):
        """Should create all expected tables."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()

            # Check tables exist
            tables = db.query("SHOW TABLES").values.flatten().tolist()
            assert "dim_cause" in tables
            assert "dim_year" in tables
            assert "fact_metrics" in tables

    def test_load_data(self, temp_db, enriched_data):
        """Should load data into database."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            stats = db.get_table_stats()
            assert stats["dim_cause"] == 13  # 13 causes
            assert stats["dim_year"] == 18  # 1999-2016
            assert stats["fact_metrics"] == 234  # 13 * 18

    def test_get_full_data(self, temp_db, enriched_data):
        """Should retrieve full data from view."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            result = db.get_full_data()
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 234
            assert "cause_name" in result.columns
            assert "category" in result.columns

    def test_get_cause_summary(self, temp_db, enriched_data):
        """Should retrieve cause summary."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            summary = db.get_cause_summary()
            assert len(summary) == 13
            assert "avg_gap" in summary.columns

    def test_query_custom(self, temp_db, enriched_data):
        """Should execute custom SQL queries."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            result = db.query("""
                SELECT cause_name, COUNT(*) as cnt
                FROM v_metrics_full
                GROUP BY cause_name
            """)

            assert len(result) == 13
            assert all(result["cnt"] == 18)  # 18 years each


class TestDataIntegrity:
    """Tests for data integrity after loading."""

    def test_death_shares_preserved(self, temp_db, enriched_data):
        """Death shares should match original data."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            result = db.query("""
                SELECT SUM(share_deaths) as total
                FROM fact_metrics
                WHERE year = 2016
            """)

            original_sum = enriched_data[enriched_data["year"] == 2016]["share_deaths"].sum()
            assert abs(result["total"].iloc[0] - original_sum) < 0.01

    def test_terrorism_zero_deaths(self, temp_db, enriched_data):
        """Terrorism should have near-zero death share."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            result = db.query("""
                SELECT AVG(share_deaths) as avg_deaths
                FROM v_metrics_full
                WHERE cause_name = 'Terrorism'
            """)

            # Terrorism deaths are effectively 0 except 2001
            assert result["avg_deaths"].iloc[0] < 0.01

    def test_heart_disease_highest_deaths(self, temp_db, enriched_data):
        """Heart disease should have highest average deaths."""
        with DatabaseManager(temp_db) as db:
            db.create_schema()
            db.load_data(enriched_data)

            result = db.query("""
                SELECT cause_name, AVG(share_deaths) as avg
                FROM v_metrics_full
                GROUP BY cause_name
                ORDER BY avg DESC
                LIMIT 1
            """)

            assert result["cause_name"].iloc[0] == "Heart disease"
