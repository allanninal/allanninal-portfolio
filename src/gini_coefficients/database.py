"""
DuckDB database for Gini Coefficients (OECD 2016).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class GiniCoefficientsDatabase(BaseDatabase):
    """Database manager for Gini coefficients data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "gini_coefficients.duckdb"
    PROJECT_NAME = "Gini Coefficients"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating Gini coefficients database schema...")

        # Main data table (time series)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gini_coefficients (
                country VARCHAR,
                year INTEGER,
                gini_post_tax DOUBLE,
                gini_pre_tax DOUBLE,
                gini_reduction DOUBLE,
                reduction_pct DOUBLE,
                inequality_tier VARCHAR,
                redistribution_tier VARCHAR
            )
        """)

        # Country summary (latest year for each country)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                year INTEGER,
                gini_post_tax DOUBLE,
                gini_pre_tax DOUBLE,
                gini_reduction DOUBLE,
                reduction_pct DOUBLE,
                inequality_tier VARCHAR,
                redistribution_tier VARCHAR
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                inequality_tier VARCHAR,
                countries INTEGER,
                avg_gini_post DOUBLE,
                avg_gini_pre DOUBLE,
                avg_reduction_pct DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["gini_coefficients", "country_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO gini_coefficients SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into gini_coefficients")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all Gini data."""
        return self.query("SELECT * FROM gini_coefficients ORDER BY country, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary (latest year for each)."""
        return self.query("SELECT * FROM country_summary ORDER BY gini_post_tax ASC")

    def get_tier_summary(self) -> pd.DataFrame:
        """Get inequality tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE inequality_tier
                WHEN 'Very Low' THEN 1
                WHEN 'Low' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'High' THEN 4
                WHEN 'Very High' THEN 5
                ELSE 6
            END
        """)

    def get_most_equal(self, limit: int = 15) -> pd.DataFrame:
        """Get most equal countries (lowest post-tax Gini)."""
        return self.query(f"""
            SELECT country, year, gini_post_tax, gini_pre_tax,
                   reduction_pct, inequality_tier
            FROM country_summary
            ORDER BY gini_post_tax ASC
            LIMIT {limit}
        """)

    def get_most_unequal(self, limit: int = 15) -> pd.DataFrame:
        """Get most unequal countries (highest post-tax Gini)."""
        return self.query(f"""
            SELECT country, year, gini_post_tax, gini_pre_tax,
                   reduction_pct, inequality_tier
            FROM country_summary
            ORDER BY gini_post_tax DESC
            LIMIT {limit}
        """)

    def get_best_redistribution(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with strongest redistribution (largest % reduction)."""
        return self.query(f"""
            SELECT country, year, gini_pre_tax, gini_post_tax,
                   reduction_pct, redistribution_tier
            FROM country_summary
            ORDER BY reduction_pct DESC
            LIMIT {limit}
        """)

    def get_country_trend(self, country: str) -> pd.DataFrame:
        """Get Gini trend for a specific country."""
        return self.query(f"""
            SELECT year, gini_post_tax, gini_pre_tax, reduction_pct
            FROM gini_coefficients
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_by_tier(self, tier: str) -> pd.DataFrame:
        """Get countries by inequality tier."""
        return self.query(f"""
            SELECT country, year, gini_post_tax, gini_pre_tax, reduction_pct
            FROM country_summary
            WHERE inequality_tier = '{tier}'
            ORDER BY gini_post_tax ASC
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get all data for a specific country."""
        return self.query(f"""
            SELECT * FROM gini_coefficients
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM gini_coefficients ORDER BY country")
        return result['country'].tolist()

    def compare_countries(self, countries: list) -> pd.DataFrame:
        """Compare multiple countries over time."""
        countries_str = "', '".join(countries)
        return self.query(f"""
            SELECT country, year, gini_post_tax, gini_pre_tax
            FROM gini_coefficients
            WHERE country IN ('{countries_str}')
            ORDER BY country, year
        """)

    def get_redistribution_comparison(self) -> pd.DataFrame:
        """Get pre vs post-tax comparison for all countries."""
        return self.query("""
            SELECT country, gini_pre_tax, gini_post_tax,
                   gini_reduction, reduction_pct, redistribution_tier
            FROM country_summary
            ORDER BY reduction_pct DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        summary = self.get_country_summary()

        most_equal = summary.iloc[0]
        most_unequal = summary.iloc[-1]

        best_redist = self.get_best_redistribution(1).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "countries": len(summary),
            "years_covered": f"{self.query('SELECT MIN(year) FROM gini_coefficients').iloc[0, 0]}-{self.query('SELECT MAX(year) FROM gini_coefficients').iloc[0, 0]}",
            "most_equal_country": most_equal['country'],
            "most_equal_gini": most_equal['gini_post_tax'],
            "most_unequal_country": most_unequal['country'],
            "most_unequal_gini": most_unequal['gini_post_tax'],
            "best_redistribution_country": best_redist['country'],
            "best_redistribution_pct": best_redist['reduction_pct'],
            "avg_gini_post": summary['gini_post_tax'].mean().round(3),
            "avg_gini_pre": summary['gini_pre_tax'].mean().round(3),
            "avg_reduction_pct": summary['reduction_pct'].mean().round(1),
            "gini_range": (most_unequal['gini_post_tax'] - most_equal['gini_post_tax']).round(3),
        }


if __name__ == "__main__":
    with GiniCoefficientsDatabase() as db:
        print("Stats:", db.get_stats())
