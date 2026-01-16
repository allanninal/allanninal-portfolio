"""
DuckDB database for Learning-Adjusted Years of Schooling data (World Bank 2018).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class LearningAdjustedDatabase(BaseDatabase):
    """Database manager for learning-adjusted years of schooling data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "learning_adjusted.duckdb"
    PROJECT_NAME = "Learning-Adjusted Years of Schooling"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating learning-adjusted database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_adjusted (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                income_group VARCHAR,
                lays DOUBLE,
                education_tier VARCHAR,
                gap_from_best DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_lays DOUBLE,
                min_lays DOUBLE,
                max_lays DOUBLE,
                std_lays DOUBLE
            )
        """)

        # Income group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS income_summary (
                income_group VARCHAR,
                countries INTEGER,
                avg_lays DOUBLE,
                min_lays DOUBLE,
                max_lays DOUBLE,
                std_lays DOUBLE
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                education_tier VARCHAR,
                countries INTEGER,
                avg_lays DOUBLE,
                min_lays DOUBLE,
                max_lays DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  income_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["learning_adjusted", "region_summary", "income_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO learning_adjusted SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into learning_adjusted")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO income_summary SELECT * FROM income_df")
        logger.info(f"Loaded {len(income_df)} rows into income_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all learning-adjusted data."""
        return self.query("SELECT * FROM learning_adjusted ORDER BY lays DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_lays DESC")

    def get_income_summary(self) -> pd.DataFrame:
        """Get income group summary."""
        return self.query("""
            SELECT * FROM income_summary
            ORDER BY CASE income_group
                WHEN 'High income' THEN 1
                WHEN 'Upper middle income' THEN 2
                WHEN 'Lower middle income' THEN 3
                WHEN 'Low income' THEN 4
                ELSE 5
            END
        """)

    def get_tier_summary(self) -> pd.DataFrame:
        """Get education tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE education_tier
                WHEN 'Excellent (11+ years)' THEN 1
                WHEN 'Good (9-11 years)' THEN 2
                WHEN 'Moderate (7-9 years)' THEN 3
                WHEN 'Low (5-7 years)' THEN 4
                WHEN 'Very Low (<5 years)' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM learning_adjusted ORDER BY country")
        return result['country'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM learning_adjusted
            WHERE country = '{country}'
        """)

    def get_top_countries(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with highest learning-adjusted years."""
        return self.query(f"""
            SELECT country, region, income_group, lays, education_tier
            FROM learning_adjusted
            ORDER BY lays DESC
            LIMIT {limit}
        """)

    def get_bottom_countries(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with lowest learning-adjusted years."""
        return self.query(f"""
            SELECT country, region, income_group, lays, education_tier
            FROM learning_adjusted
            ORDER BY lays ASC
            LIMIT {limit}
        """)

    def get_by_tier(self, tier: str) -> pd.DataFrame:
        """Get countries by education tier."""
        return self.query(f"""
            SELECT country, region, income_group, lays, gap_from_best
            FROM learning_adjusted
            WHERE education_tier = '{tier}'
            ORDER BY lays DESC
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT country, income_group, lays, education_tier, gap_from_best
            FROM learning_adjusted
            WHERE region = '{region}'
            ORDER BY lays DESC
        """)

    def get_by_income(self, income_group: str) -> pd.DataFrame:
        """Get countries by income group."""
        return self.query(f"""
            SELECT country, region, lays, education_tier, gap_from_best
            FROM learning_adjusted
            WHERE income_group = '{income_group}'
            ORDER BY lays DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        global_avg = self.query("""
            SELECT AVG(lays) as avg FROM learning_adjusted
        """)['avg'].iloc[0]

        best = self.query("""
            SELECT country, lays FROM learning_adjusted
            ORDER BY lays DESC LIMIT 1
        """).iloc[0]

        lowest = self.query("""
            SELECT country, lays FROM learning_adjusted
            ORDER BY lays ASC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM learning_adjusted").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT country) FROM learning_adjusted").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "income_groups": self.conn.execute("SELECT COUNT(*) FROM income_summary").fetchone()[0],
            "global_avg": round(global_avg, 1) if global_avg else 0,
            "best_country": best['country'],
            "best_lays": round(best['lays'], 1),
            "lowest_country": lowest['country'],
            "lowest_lays": round(lowest['lays'], 1),
        }


if __name__ == "__main__":
    with LearningAdjustedDatabase() as db:
        print("Stats:", db.get_stats())
