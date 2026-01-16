"""
DuckDB database for Female Labor Force Participation data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class FemaleLaborDatabase(BaseDatabase):
    """Database manager for female labor force participation data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "female_labor.duckdb"
    PROJECT_NAME = "Female Labor Force Participation"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating female labor database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS labor_participation (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                participation_rate DOUBLE,
                decade VARCHAR
            )
        """)

        # Country summary (latest + historical)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                region VARCHAR,
                latest_year INTEGER,
                latest_rate DOUBLE,
                earliest_year INTEGER,
                earliest_rate DOUBLE,
                rate_change DOUBLE,
                data_points INTEGER,
                avg_rate DOUBLE,
                max_rate DOUBLE,
                min_rate DOUBLE
            )
        """)

        # Regional summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_rate DOUBLE,
                min_rate DOUBLE,
                max_rate DOUBLE,
                total_data_points INTEGER
            )
        """)

        # Decade trends
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decade_summary (
                decade VARCHAR,
                avg_rate DOUBLE,
                countries_with_data INTEGER,
                min_rate DOUBLE,
                max_rate DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, decade_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["labor_participation", "country_summary", "region_summary", "decade_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO labor_participation SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into labor_participation")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO decade_summary SELECT * FROM decade_df")
        logger.info(f"Loaded {len(decade_df)} rows into decade_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all labor participation data."""
        return self.query("SELECT * FROM labor_participation ORDER BY country, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM country_summary ORDER BY latest_rate DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_rate DESC")

    def get_decade_summary(self) -> pd.DataFrame:
        """Get decade trends."""
        return self.query("SELECT * FROM decade_summary ORDER BY decade")

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM labor_participation ORDER BY country")
        return result['country'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM labor_participation
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_top_countries(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with highest latest participation rate."""
        return self.query(f"""
            SELECT country, region, latest_rate, rate_change
            FROM country_summary
            WHERE latest_rate IS NOT NULL
            ORDER BY latest_rate DESC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with largest rate increase."""
        return self.query(f"""
            SELECT country, region, earliest_rate, latest_rate, rate_change
            FROM country_summary
            WHERE rate_change IS NOT NULL AND earliest_rate IS NOT NULL
            ORDER BY rate_change DESC
            LIMIT {limit}
        """)

    def get_historical_leaders(self) -> pd.DataFrame:
        """Get countries with data going back furthest."""
        return self.query("""
            SELECT country, earliest_year, latest_year, data_points, rate_change
            FROM country_summary
            ORDER BY earliest_year ASC
            LIMIT 10
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest_avg = self.query("""
            SELECT AVG(latest_rate) as avg FROM country_summary
        """)['avg'].iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM labor_participation").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT country) FROM labor_participation").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": self.query("SELECT MIN(year) as min_y, MAX(year) as max_y FROM labor_participation").iloc[0].tolist(),
            "latest_avg_rate": round(latest_avg, 1) if latest_avg else 0,
        }


if __name__ == "__main__":
    with FemaleLaborDatabase() as db:
        print("Stats:", db.get_stats())
