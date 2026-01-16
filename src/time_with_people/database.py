"""
DuckDB database for American Time Use Survey data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class TimeWithPeopleDatabase(BaseDatabase):
    """Database manager for time use survey data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "time_with_people.duckdb"
    PROJECT_NAME = "Time With People"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating time with people database schema...")

        # Main data table - time by age
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS time_by_age (
                age INTEGER,
                alone DOUBLE,
                children DOUBLE,
                coworkers DOUBLE,
                family DOUBLE,
                friends DOUBLE,
                other DOUBLE,
                partner DOUBLE,
                unclassified DOUBLE,
                age_group VARCHAR,
                total_accounted DOUBLE
            )
        """)

        # Companion summary statistics
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS companion_summary (
                companion VARCHAR,
                avg_minutes DOUBLE,
                min_minutes DOUBLE,
                max_minutes DOUBLE,
                peak_age INTEGER,
                decline_age INTEGER
            )
        """)

        # Age group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS age_group_summary (
                age_group VARCHAR,
                age_range VARCHAR,
                alone DOUBLE,
                children DOUBLE,
                coworkers DOUBLE,
                family DOUBLE,
                friends DOUBLE,
                partner DOUBLE,
                total_social DOUBLE
            )
        """)

        # Long-format data for easier visualization
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS time_long_format (
                age INTEGER,
                companion VARCHAR,
                minutes DOUBLE,
                age_group VARCHAR
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, companion_df: pd.DataFrame,
                  age_group_df: pd.DataFrame, long_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["time_by_age", "companion_summary", "age_group_summary", "time_long_format"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO time_by_age SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into time_by_age")

        self.conn.execute("INSERT INTO companion_summary SELECT * FROM companion_df")
        logger.info(f"Loaded {len(companion_df)} rows into companion_summary")

        self.conn.execute("INSERT INTO age_group_summary SELECT * FROM age_group_df")
        logger.info(f"Loaded {len(age_group_df)} rows into age_group_summary")

        self.conn.execute("INSERT INTO time_long_format SELECT * FROM long_df")
        logger.info(f"Loaded {len(long_df)} rows into time_long_format")

    def get_full_data(self) -> pd.DataFrame:
        """Get all time use data (required by base class)."""
        return self.query("SELECT * FROM time_by_age ORDER BY age")

    def get_time_by_age(self) -> pd.DataFrame:
        """Get all time use data by age."""
        return self.query("SELECT * FROM time_by_age ORDER BY age")

    def get_companion_summary(self) -> pd.DataFrame:
        """Get companion type summary statistics."""
        return self.query("SELECT * FROM companion_summary ORDER BY avg_minutes DESC")

    def get_age_group_summary(self) -> pd.DataFrame:
        """Get age group summary."""
        return self.query("""
            SELECT * FROM age_group_summary
            ORDER BY CASE age_group
                WHEN 'Teen (15-19)' THEN 1
                WHEN 'Young Adult (20-29)' THEN 2
                WHEN 'Adult (30-39)' THEN 3
                WHEN 'Middle Age (40-49)' THEN 4
                WHEN 'Mature Adult (50-59)' THEN 5
                WHEN 'Senior (60-69)' THEN 6
                WHEN 'Elderly (70+)' THEN 7
            END
        """)

    def get_long_format(self) -> pd.DataFrame:
        """Get data in long format for visualization."""
        return self.query("SELECT * FROM time_long_format ORDER BY age, companion")

    def get_time_for_companion(self, companion: str) -> pd.DataFrame:
        """Get time series for a specific companion type."""
        return self.query(f"""
            SELECT age, minutes
            FROM time_long_format
            WHERE companion = '{companion}'
            ORDER BY age
        """)

    def get_peak_ages(self) -> pd.DataFrame:
        """Get age where each companion type peaks."""
        return self.query("""
            SELECT companion, peak_age, max_minutes
            FROM companion_summary
            ORDER BY peak_age
        """)

    def get_time_at_age(self, age: int) -> pd.DataFrame:
        """Get time distribution at a specific age."""
        return self.query(f"""
            SELECT companion, minutes
            FROM time_long_format
            WHERE age = {age}
            ORDER BY minutes DESC
        """)

    def get_crossover_points(self) -> pd.DataFrame:
        """Find ages where companion types cross over."""
        return self.query("""
            WITH ranked AS (
                SELECT age, companion, minutes,
                       LAG(minutes) OVER (PARTITION BY companion ORDER BY age) as prev_minutes
                FROM time_long_format
            )
            SELECT age, companion, minutes, prev_minutes
            FROM ranked
            WHERE prev_minutes IS NOT NULL
            ORDER BY age, companion
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        ages = self.query("SELECT MIN(age) as min_a, MAX(age) as max_a FROM time_by_age").iloc[0]

        # Find when alone time exceeds all social time
        alone_peak = self.query("""
            SELECT age, alone FROM time_by_age
            WHERE alone = (SELECT MAX(alone) FROM time_by_age)
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM time_by_age").fetchone()[0],
            "age_range": [int(ages['min_a']), int(ages['max_a'])],
            "companion_types": self.conn.execute("SELECT COUNT(DISTINCT companion) FROM time_long_format").fetchone()[0],
            "peak_alone_age": int(alone_peak['age']),
            "peak_alone_minutes": round(alone_peak['alone'], 1),
        }


if __name__ == "__main__":
    with TimeWithPeopleDatabase() as db:
        print("Stats:", db.get_stats())
