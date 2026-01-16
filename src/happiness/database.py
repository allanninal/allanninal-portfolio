"""
DuckDB database for World Happiness Report data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class HappinessDatabase(BaseDatabase):
    """Database manager for happiness data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "happiness.duckdb"
    PROJECT_NAME = "World Happiness"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating happiness database schema...")

        # Main fact table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS happiness_data (
                country VARCHAR,
                year INTEGER,
                happiness_score DOUBLE,
                region VARCHAR,
                happiness_tier VARCHAR,
                yoy_change DOUBLE,
                country_avg DOUBLE,
                rank INTEGER
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                region VARCHAR,
                happiness_score DOUBLE,
                happiness_tier VARCHAR,
                rank INTEGER
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                avg_score DOUBLE,
                std_score DOUBLE,
                min_score DOUBLE,
                max_score DOUBLE,
                observations INTEGER,
                countries INTEGER
            )
        """)

        # Year summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                global_avg DOUBLE,
                std DOUBLE,
                min DOUBLE,
                max DOUBLE,
                countries INTEGER
            )
        """)

        # Useful views
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_latest_rankings AS
            SELECT country, region, happiness_score, happiness_tier, rank
            FROM country_summary
            ORDER BY rank
        """)

        self.conn.execute("""
            CREATE OR REPLACE VIEW v_region_comparison AS
            SELECT
                region,
                avg_score,
                countries,
                RANK() OVER (ORDER BY avg_score DESC) as region_rank
            FROM region_summary
            ORDER BY avg_score DESC
        """)

        logger.info("Schema created successfully")

    def load_data(self, enriched_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, year_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        # Clear existing
        for table in ["happiness_data", "country_summary", "region_summary", "year_summary"]:
            self.conn.execute(f"DELETE FROM {table}")

        # Load each table
        self.conn.execute("INSERT INTO happiness_data SELECT * FROM enriched_df")
        logger.info(f"Loaded {len(enriched_df)} rows into happiness_data")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO year_summary SELECT * FROM year_df")
        logger.info(f"Loaded {len(year_df)} rows into year_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all happiness data."""
        return self.query("SELECT * FROM happiness_data ORDER BY year, rank")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM v_latest_rankings")

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM v_region_comparison")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year summary."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_country_history(self, country: str) -> pd.DataFrame:
        """Get historical data for a country."""
        return self.query(f"""
            SELECT year, happiness_score, yoy_change, rank
            FROM happiness_data
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        return {
            "project": self.PROJECT_NAME,
            "happiness_data": self.conn.execute("SELECT COUNT(*) FROM happiness_data").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(*) FROM country_summary").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": self.conn.execute("SELECT COUNT(*) FROM year_summary").fetchone()[0],
        }


if __name__ == "__main__":
    with HappinessDatabase() as db:
        print("Stats:", db.get_stats())
