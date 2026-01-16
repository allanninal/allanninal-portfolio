"""
DuckDB database for Child Mortality Rates (Gapminder v10, 2017).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class ChildMortalityDatabase(BaseDatabase):
    """Database manager for child mortality data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "child_mortality.duckdb"
    PROJECT_NAME = "Child Mortality Rates"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating child mortality database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS child_mortality (
                country VARCHAR,
                year INTEGER,
                mortality_rate DOUBLE,
                region VARCHAR,
                mortality_tier VARCHAR,
                improvement_pts DOUBLE,
                improvement_pct DOUBLE,
                improvement_tier VARCHAR
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_rate DOUBLE,
                min_rate DOUBLE,
                max_rate DOUBLE,
                avg_improvement_pct DOUBLE
            )
        """)

        # Year summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS year_summary (
                year INTEGER,
                countries INTEGER,
                avg_rate DOUBLE,
                min_rate DOUBLE,
                max_rate DOUBLE
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                mortality_tier VARCHAR,
                countries INTEGER,
                avg_rate DOUBLE,
                avg_improvement_pct DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  year_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["child_mortality", "region_summary", "year_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO child_mortality SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into child_mortality")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO year_summary SELECT * FROM year_df")
        logger.info(f"Loaded {len(year_df)} rows into year_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all child mortality data."""
        return self.query("SELECT * FROM child_mortality ORDER BY year, mortality_rate")

    def get_latest_data(self) -> pd.DataFrame:
        """Get 2016 data (most recent)."""
        return self.query("""
            SELECT * FROM child_mortality
            WHERE year = 2016
            ORDER BY mortality_rate ASC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_rate ASC")

    def get_year_summary(self) -> pd.DataFrame:
        """Get year summary showing global trends."""
        return self.query("SELECT * FROM year_summary ORDER BY year")

    def get_tier_summary(self) -> pd.DataFrame:
        """Get mortality tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE mortality_tier
                WHEN 'Very Low' THEN 1
                WHEN 'Low' THEN 2
                WHEN 'Moderate' THEN 3
                WHEN 'High' THEN 4
                WHEN 'Very High' THEN 5
                ELSE 6
            END
        """)

    def get_lowest_mortality(self, year: int = 2016, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest child mortality."""
        return self.query(f"""
            SELECT country, region, mortality_rate, mortality_tier, improvement_pct
            FROM child_mortality
            WHERE year = {year}
            ORDER BY mortality_rate ASC
            LIMIT {limit}
        """)

    def get_highest_mortality(self, year: int = 2016, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest child mortality."""
        return self.query(f"""
            SELECT country, region, mortality_rate, mortality_tier, improvement_pct
            FROM child_mortality
            WHERE year = {year}
            ORDER BY mortality_rate DESC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most improvement 1950-2016."""
        return self.query(f"""
            SELECT country, region, improvement_pct, improvement_pts, improvement_tier,
                   mortality_rate as rate_2016
            FROM child_mortality
            WHERE year = 2016 AND improvement_pct IS NOT NULL
            ORDER BY improvement_pct DESC
            LIMIT {limit}
        """)

    def get_least_improved(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with least improvement 1950-2016."""
        return self.query(f"""
            SELECT country, region, improvement_pct, improvement_pts, improvement_tier,
                   mortality_rate as rate_2016
            FROM child_mortality
            WHERE year = 2016 AND improvement_pct IS NOT NULL
            ORDER BY improvement_pct ASC
            LIMIT {limit}
        """)

    def get_country_trend(self, country: str) -> pd.DataFrame:
        """Get child mortality trend for a specific country."""
        return self.query(f"""
            SELECT year, mortality_rate, mortality_tier
            FROM child_mortality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_by_region(self, region: str, year: int = 2016) -> pd.DataFrame:
        """Get countries by region for a specific year."""
        return self.query(f"""
            SELECT country, mortality_rate, mortality_tier, improvement_pct
            FROM child_mortality
            WHERE region = '{region}' AND year = {year}
            ORDER BY mortality_rate ASC
        """)

    def get_by_tier(self, tier: str, year: int = 2016) -> pd.DataFrame:
        """Get countries by mortality tier for a specific year."""
        return self.query(f"""
            SELECT country, region, mortality_rate, improvement_pct
            FROM child_mortality
            WHERE mortality_tier = '{tier}' AND year = {year}
            ORDER BY mortality_rate ASC
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get all data for a specific country."""
        return self.query(f"""
            SELECT * FROM child_mortality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM child_mortality ORDER BY country")
        return result['country'].tolist()

    def get_regions_list(self):
        """Get list of all regions."""
        result = self.query("SELECT DISTINCT region FROM child_mortality ORDER BY region")
        return result['region'].tolist()

    def get_global_trend(self) -> pd.DataFrame:
        """Get global child mortality trend over time (milestone years)."""
        return self.query("""
            SELECT year, avg_rate, min_rate, max_rate
            FROM year_summary
            ORDER BY year
        """)

    def get_historical_trend(self, start_year: int = 1800, end_year: int = 2016) -> pd.DataFrame:
        """Get annual global average for time series."""
        return self.query(f"""
            SELECT year, AVG(mortality_rate) as avg_rate,
                   MIN(mortality_rate) as min_rate,
                   MAX(mortality_rate) as max_rate,
                   COUNT(DISTINCT country) as countries
            FROM child_mortality
            WHERE year >= {start_year} AND year <= {end_year}
            GROUP BY year
            ORDER BY year
        """)

    def compare_countries(self, countries: list) -> pd.DataFrame:
        """Compare multiple countries over time."""
        countries_str = "', '".join(countries)
        return self.query(f"""
            SELECT country, year, mortality_rate
            FROM child_mortality
            WHERE country IN ('{countries_str}')
            ORDER BY country, year
        """)

    def get_era_comparison(self) -> pd.DataFrame:
        """Compare mortality rates across different eras."""
        return self.query("""
            SELECT
                CASE
                    WHEN year <= 1900 THEN '1800-1900'
                    WHEN year <= 1950 THEN '1901-1950'
                    WHEN year <= 1980 THEN '1951-1980'
                    WHEN year <= 2000 THEN '1981-2000'
                    ELSE '2001-2016'
                END as era,
                AVG(mortality_rate) as avg_rate,
                MIN(mortality_rate) as min_rate,
                MAX(mortality_rate) as max_rate,
                COUNT(DISTINCT country) as countries
            FROM child_mortality
            GROUP BY era
            ORDER BY era
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest = self.get_latest_data()

        lowest = latest.iloc[0]
        highest = latest.iloc[-1]

        most_improved_df = self.get_most_improved(1)
        most_improved = most_improved_df.iloc[0] if len(most_improved_df) > 0 else None

        # Get 1950 average
        avg_1950 = self.query("SELECT AVG(mortality_rate) as avg FROM child_mortality WHERE year = 1950")
        avg_2016 = self.query("SELECT AVG(mortality_rate) as avg FROM child_mortality WHERE year = 2016")

        return {
            "project": self.PROJECT_NAME,
            "countries": len(latest),
            "years_covered": "1800-2016",
            "lowest_mortality_country": lowest['country'],
            "lowest_mortality": lowest['mortality_rate'],
            "highest_mortality_country": highest['country'],
            "highest_mortality": highest['mortality_rate'],
            "most_improved_country": most_improved['country'] if most_improved is not None else "N/A",
            "most_improved_pct": most_improved['improvement_pct'] if most_improved is not None else 0,
            "avg_mortality_2016": latest['mortality_rate'].mean().round(1),
            "avg_mortality_1950": avg_1950['avg'].values[0].round(1) if len(avg_1950) > 0 else 0,
            "global_improvement_pct": ((avg_1950['avg'].values[0] - avg_2016['avg'].values[0]) / avg_1950['avg'].values[0] * 100).round(1),
            "mortality_range": highest['mortality_rate'] - lowest['mortality_rate'],
        }


if __name__ == "__main__":
    with ChildMortalityDatabase() as db:
        print("Stats:", db.get_stats())
