"""
DuckDB database for Gender Wage Gap data (OECD 2017).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class GenderWageGapDatabase(BaseDatabase):
    """Database manager for gender wage gap data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "gender_wage_gap.duckdb"
    PROJECT_NAME = "Gender Wage Gap"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating gender wage gap database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS wage_gap (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                wage_gap DOUBLE,
                decade VARCHAR,
                gap_tier VARCHAR
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                region VARCHAR,
                latest_year INTEGER,
                latest_gap DOUBLE,
                earliest_year INTEGER,
                earliest_gap DOUBLE,
                gap_change DOUBLE,
                data_points INTEGER,
                avg_gap DOUBLE,
                min_gap DOUBLE,
                max_gap DOUBLE,
                gap_tier VARCHAR
            )
        """)

        # Regional summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_gap DOUBLE,
                min_gap DOUBLE,
                max_gap DOUBLE
            )
        """)

        # Decade summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decade_summary (
                decade VARCHAR,
                avg_gap DOUBLE,
                countries_with_data INTEGER,
                min_gap DOUBLE,
                max_gap DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, decade_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["wage_gap", "country_summary", "region_summary", "decade_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO wage_gap SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into wage_gap")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO decade_summary SELECT * FROM decade_df")
        logger.info(f"Loaded {len(decade_df)} rows into decade_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all wage gap data."""
        return self.query("SELECT * FROM wage_gap ORDER BY country, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM country_summary ORDER BY latest_gap ASC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_gap ASC")

    def get_decade_summary(self) -> pd.DataFrame:
        """Get decade trends."""
        return self.query("SELECT * FROM decade_summary ORDER BY decade")

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM wage_gap ORDER BY country")
        return result['country'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM wage_gap
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_lowest_gap(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with lowest wage gap (most equal)."""
        return self.query(f"""
            SELECT country, region, latest_gap, gap_change
            FROM country_summary
            WHERE latest_gap IS NOT NULL
            ORDER BY latest_gap ASC
            LIMIT {limit}
        """)

    def get_highest_gap(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with highest wage gap (least equal)."""
        return self.query(f"""
            SELECT country, region, latest_gap, gap_change
            FROM country_summary
            WHERE latest_gap IS NOT NULL
            ORDER BY latest_gap DESC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with largest gap reduction."""
        return self.query(f"""
            SELECT country, region, earliest_gap, latest_gap, gap_change
            FROM country_summary
            WHERE gap_change IS NOT NULL
            ORDER BY gap_change ASC
            LIMIT {limit}
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest_avg = self.query("""
            SELECT AVG(latest_gap) as avg FROM country_summary
        """)['avg'].iloc[0]

        lowest = self.query("""
            SELECT country, latest_gap FROM country_summary
            ORDER BY latest_gap ASC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM wage_gap").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT country) FROM wage_gap").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": self.query("SELECT MIN(year) as min_y, MAX(year) as max_y FROM wage_gap").iloc[0].tolist(),
            "latest_avg_gap": round(latest_avg, 1) if latest_avg else 0,
            "most_equal_country": lowest['country'],
            "most_equal_gap": round(lowest['latest_gap'], 1),
        }


if __name__ == "__main__":
    with GenderWageGapDatabase() as db:
        print("Stats:", db.get_stats())
