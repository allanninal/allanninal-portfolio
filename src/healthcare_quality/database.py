"""
DuckDB database for Healthcare Access and Quality Index (IHME 2017).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class HealthcareQualityDatabase(BaseDatabase):
    """Database manager for healthcare quality index data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "healthcare_quality.duckdb"
    PROJECT_NAME = "Healthcare Access and Quality Index"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating healthcare quality database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS healthcare_quality (
                country VARCHAR,
                year INTEGER,
                haq_index DOUBLE,
                region VARCHAR,
                haq_tier VARCHAR,
                improvement DOUBLE,
                improvement_pct DOUBLE,
                improvement_tier VARCHAR
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_haq DOUBLE,
                min_haq DOUBLE,
                max_haq DOUBLE,
                avg_improvement DOUBLE
            )
        """)

        # Year summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                countries INTEGER,
                avg_haq DOUBLE,
                min_haq DOUBLE,
                max_haq DOUBLE
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                haq_tier VARCHAR,
                countries INTEGER,
                avg_haq DOUBLE,
                avg_improvement DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  year_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["healthcare_quality", "region_summary", "year_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO healthcare_quality SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into healthcare_quality")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO year_summary SELECT * FROM year_df")
        logger.info(f"Loaded {len(year_df)} rows into year_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all healthcare quality data."""
        return self.query("SELECT * FROM healthcare_quality ORDER BY year, haq_index DESC")

    def get_latest_data(self) -> pd.DataFrame:
        """Get 2015 data (most recent)."""
        return self.query("""
            SELECT * FROM healthcare_quality
            WHERE year = 2015
            ORDER BY haq_index DESC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_haq DESC")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year summary showing global trends."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_tier_summary(self) -> pd.DataFrame:
        """Get HAQ tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE haq_tier
                WHEN 'Very High' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'Low' THEN 4
                WHEN 'Very Low' THEN 5
                ELSE 6
            END
        """)

    def get_top_countries(self, year: int = 2015, limit: int = 20) -> pd.DataFrame:
        """Get top countries by HAQ index."""
        return self.query(f"""
            SELECT country, region, haq_index, haq_tier, improvement
            FROM healthcare_quality
            WHERE year = {year}
            ORDER BY haq_index DESC
            LIMIT {limit}
        """)

    def get_bottom_countries(self, year: int = 2015, limit: int = 20) -> pd.DataFrame:
        """Get bottom countries by HAQ index."""
        return self.query(f"""
            SELECT country, region, haq_index, haq_tier, improvement
            FROM healthcare_quality
            WHERE year = {year}
            ORDER BY haq_index ASC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most improvement 1990-2015."""
        return self.query(f"""
            SELECT country, region, improvement, improvement_pct, improvement_tier,
                   haq_index as haq_2015
            FROM healthcare_quality
            WHERE year = 2015
            ORDER BY improvement DESC
            LIMIT {limit}
        """)

    def get_least_improved(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with least improvement 1990-2015."""
        return self.query(f"""
            SELECT country, region, improvement, improvement_pct, improvement_tier,
                   haq_index as haq_2015
            FROM healthcare_quality
            WHERE year = 2015
            ORDER BY improvement ASC
            LIMIT {limit}
        """)

    def get_country_trend(self, country: str) -> pd.DataFrame:
        """Get HAQ index trend for a specific country."""
        return self.query(f"""
            SELECT year, haq_index, haq_tier
            FROM healthcare_quality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_by_region(self, region: str, year: int = 2015) -> pd.DataFrame:
        """Get countries by region for a specific year."""
        return self.query(f"""
            SELECT country, haq_index, haq_tier, improvement
            FROM healthcare_quality
            WHERE region = '{region}' AND year = {year}
            ORDER BY haq_index DESC
        """)

    def get_by_tier(self, tier: str, year: int = 2015) -> pd.DataFrame:
        """Get countries by HAQ tier for a specific year."""
        return self.query(f"""
            SELECT country, region, haq_index, improvement
            FROM healthcare_quality
            WHERE haq_tier = '{tier}' AND year = {year}
            ORDER BY haq_index DESC
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get all data for a specific country."""
        return self.query(f"""
            SELECT * FROM healthcare_quality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM healthcare_quality ORDER BY country")
        return result['country'].tolist()

    def get_regions_list(self):
        """Get list of all regions."""
        result = self.query("SELECT DISTINCT region FROM healthcare_quality ORDER BY region")
        return result['region'].tolist()

    def get_global_trend(self) -> pd.DataFrame:
        """Get global HAQ trend over time."""
        return self.query("""
            SELECT year, avg_haq, min_haq, max_haq
            FROM year_summary
            ORDER BY year
        """)

    def compare_countries(self, countries: list) -> pd.DataFrame:
        """Compare multiple countries over time."""
        countries_str = "', '".join(countries)
        return self.query(f"""
            SELECT country, year, haq_index
            FROM healthcare_quality
            WHERE country IN ('{countries_str}')
            ORDER BY country, year
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest = self.get_latest_data()

        highest = latest.iloc[0]
        lowest = latest.iloc[-1]

        most_improved = self.get_most_improved(1).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "countries": len(latest),
            "years_covered": "1990-2015",
            "time_points": 6,
            "highest_haq_country": highest['country'],
            "highest_haq": highest['haq_index'],
            "lowest_haq_country": lowest['country'],
            "lowest_haq": lowest['haq_index'],
            "most_improved_country": most_improved['country'],
            "most_improved_points": most_improved['improvement'],
            "avg_haq_2015": latest['haq_index'].mean().round(1),
            "avg_improvement": latest['improvement'].mean().round(1),
            "haq_range": highest['haq_index'] - lowest['haq_index'],
        }


if __name__ == "__main__":
    with HealthcareQualityDatabase() as db:
        print("Stats:", db.get_stats())
