"""
DuckDB database for Mobile Data Pricing data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class MobileDataDatabase(BaseDatabase):
    """Database manager for mobile data pricing."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "mobile_data.duckdb"
    PROJECT_NAME = "Mobile Data Pricing"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating mobile data database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS mobile_data (
                country VARCHAR,
                year INTEGER,
                cost_pct_gni DOUBLE,
                region VARCHAR,
                affordability_tier VARCHAR,
                ratio_to_un_target DOUBLE,
                rank INTEGER,
                days_of_income_per_gb DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                avg_cost DOUBLE,
                median_cost DOUBLE,
                min_cost DOUBLE,
                max_cost DOUBLE,
                std_cost DOUBLE,
                observations INTEGER,
                countries INTEGER
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                affordability_tier VARCHAR,
                countries INTEGER,
                avg_cost DOUBLE,
                min_cost DOUBLE,
                max_cost DOUBLE
            )
        """)

        # Useful views
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_affordability_rankings AS
            SELECT country, region, cost_pct_gni, affordability_tier, rank,
                   days_of_income_per_gb, ratio_to_un_target
            FROM mobile_data
            ORDER BY rank
        """)

        self.conn.execute("""
            CREATE OR REPLACE VIEW v_region_comparison AS
            SELECT
                region,
                avg_cost,
                countries,
                RANK() OVER (ORDER BY avg_cost ASC) as region_rank
            FROM region_summary
            ORDER BY avg_cost ASC
        """)

        logger.info("Schema created successfully")

    def load_data(self, enriched_df: pd.DataFrame, region_df: pd.DataFrame,
                  tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        # Clear existing
        for table in ["mobile_data", "region_summary", "tier_summary"]:
            self.conn.execute(f"DELETE FROM {table}")

        # Load each table
        self.conn.execute("INSERT INTO mobile_data SELECT * FROM enriched_df")
        logger.info(f"Loaded {len(enriched_df)} rows into mobile_data")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all mobile data."""
        return self.query("SELECT * FROM mobile_data ORDER BY rank")

    def get_rankings(self) -> pd.DataFrame:
        """Get affordability rankings."""
        return self.query("SELECT * FROM v_affordability_rankings")

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_cost")

    def get_tier_summary(self) -> pd.DataFrame:
        """Get tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE affordability_tier
                WHEN 'Affordable' THEN 1
                WHEN 'Moderately Affordable' THEN 2
                WHEN 'Expensive' THEN 3
                WHEN 'Unaffordable' THEN 4
            END
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        return {
            "project": self.PROJECT_NAME,
            "mobile_data": self.conn.execute("SELECT COUNT(*) FROM mobile_data").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "tiers": self.conn.execute("SELECT COUNT(*) FROM tier_summary").fetchone()[0],
        }


if __name__ == "__main__":
    with MobileDataDatabase() as db:
        print("Stats:", db.get_stats())
