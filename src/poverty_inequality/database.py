"""
DuckDB database for World Bank Poverty and Inequality Platform (PIP).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class PovertyInequalityDatabase(BaseDatabase):
    """Database manager for poverty and inequality data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "poverty_inequality.duckdb"
    PROJECT_NAME = "Poverty and Inequality Platform"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating poverty and inequality database schema...")

        # Main time series data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS poverty_inequality (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                reporting_level VARCHAR,
                welfare_type VARCHAR,
                extreme_poverty_rate DOUBLE,
                lower_mid_poverty_rate DOUBLE,
                upper_mid_poverty_rate DOUBLE,
                poverty_gap_index DOUBLE,
                gini DOUBLE,
                mean DOUBLE,
                median DOUBLE,
                extreme_poverty_count DOUBLE,
                lower_mid_poverty_count DOUBLE,
                upper_mid_poverty_count DOUBLE,
                poverty_tier VARCHAR,
                inequality_tier VARCHAR,
                decile1_share DOUBLE,
                decile10_share DOUBLE,
                palma_ratio DOUBLE,
                p90_p10_ratio DOUBLE
            )
        """)

        # Latest year data for each country
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_latest (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                reporting_level VARCHAR,
                welfare_type VARCHAR,
                extreme_poverty_rate DOUBLE,
                lower_mid_poverty_rate DOUBLE,
                upper_mid_poverty_rate DOUBLE,
                poverty_gap_index DOUBLE,
                gini DOUBLE,
                mean DOUBLE,
                median DOUBLE,
                extreme_poverty_count DOUBLE,
                lower_mid_poverty_count DOUBLE,
                upper_mid_poverty_count DOUBLE,
                poverty_tier VARCHAR,
                inequality_tier VARCHAR,
                decile1_share DOUBLE,
                decile10_share DOUBLE,
                palma_ratio DOUBLE,
                p90_p10_ratio DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_extreme_poverty DOUBLE,
                avg_lower_mid_poverty DOUBLE,
                avg_gini DOUBLE,
                avg_mean_income DOUBLE,
                total_extreme_poor DOUBLE
            )
        """)

        # Poverty tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS poverty_tier_summary (
                poverty_tier VARCHAR,
                countries INTEGER,
                avg_extreme_poverty DOUBLE,
                avg_gini DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, latest_df: pd.DataFrame,
                  region_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["poverty_inequality", "country_latest", "region_summary", "poverty_tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO poverty_inequality SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into poverty_inequality")

        self.conn.execute("INSERT INTO country_latest SELECT * FROM latest_df")
        logger.info(f"Loaded {len(latest_df)} rows into country_latest")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO poverty_tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into poverty_tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all poverty and inequality data."""
        return self.query("SELECT * FROM poverty_inequality ORDER BY country, year")

    def get_country_latest(self) -> pd.DataFrame:
        """Get latest data for each country."""
        return self.query("""
            SELECT * FROM country_latest
            ORDER BY extreme_poverty_rate DESC
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary statistics."""
        return self.query("""
            SELECT * FROM region_summary
            ORDER BY avg_extreme_poverty DESC
        """)

    def get_poverty_tier_summary(self) -> pd.DataFrame:
        """Get poverty tier summary."""
        return self.query("""
            SELECT * FROM poverty_tier_summary
            ORDER BY CASE poverty_tier
                WHEN 'Extreme (40%+)' THEN 1
                WHEN 'High (20-40%)' THEN 2
                WHEN 'Moderate (5-20%)' THEN 3
                WHEN 'Low (1-5%)' THEN 4
                WHEN 'Very Low (<1%)' THEN 5
                ELSE 6
            END
        """)

    def get_highest_poverty(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with highest extreme poverty rates."""
        return self.query(f"""
            SELECT country, year, region, extreme_poverty_rate,
                   lower_mid_poverty_rate, gini, poverty_tier
            FROM country_latest
            WHERE extreme_poverty_rate IS NOT NULL
            ORDER BY extreme_poverty_rate DESC
            LIMIT {limit}
        """)

    def get_lowest_poverty(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with lowest extreme poverty rates."""
        return self.query(f"""
            SELECT country, year, region, extreme_poverty_rate,
                   lower_mid_poverty_rate, gini, poverty_tier
            FROM country_latest
            WHERE extreme_poverty_rate IS NOT NULL
            ORDER BY extreme_poverty_rate ASC
            LIMIT {limit}
        """)

    def get_most_unequal(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with highest Gini coefficients."""
        return self.query(f"""
            SELECT country, year, region, gini, extreme_poverty_rate,
                   decile1_share, decile10_share, inequality_tier
            FROM country_latest
            WHERE gini IS NOT NULL
            ORDER BY gini DESC
            LIMIT {limit}
        """)

    def get_most_equal(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with lowest Gini coefficients."""
        return self.query(f"""
            SELECT country, year, region, gini, extreme_poverty_rate,
                   decile1_share, decile10_share, inequality_tier
            FROM country_latest
            WHERE gini IS NOT NULL
            ORDER BY gini ASC
            LIMIT {limit}
        """)

    def get_country_trend(self, country: str) -> pd.DataFrame:
        """Get poverty and inequality trend for a specific country."""
        return self.query(f"""
            SELECT year, extreme_poverty_rate, lower_mid_poverty_rate,
                   upper_mid_poverty_rate, gini, mean, median
            FROM poverty_inequality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get all data for a specific country."""
        return self.query(f"""
            SELECT * FROM poverty_inequality
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM poverty_inequality ORDER BY country")
        return result['country'].tolist()

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT country, year, extreme_poverty_rate, lower_mid_poverty_rate,
                   gini, mean, poverty_tier
            FROM country_latest
            WHERE region = '{region}'
            ORDER BY extreme_poverty_rate DESC
        """)

    def compare_countries(self, countries: list) -> pd.DataFrame:
        """Compare multiple countries over time."""
        countries_str = "', '".join(countries)
        return self.query(f"""
            SELECT country, year, extreme_poverty_rate, lower_mid_poverty_rate, gini
            FROM poverty_inequality
            WHERE country IN ('{countries_str}')
            ORDER BY country, year
        """)

    def get_global_trend(self) -> pd.DataFrame:
        """Get global poverty trend over time."""
        return self.query("""
            SELECT year,
                   AVG(extreme_poverty_rate) as avg_extreme_poverty,
                   AVG(lower_mid_poverty_rate) as avg_lower_mid_poverty,
                   AVG(gini) as avg_gini,
                   COUNT(DISTINCT country) as countries
            FROM poverty_inequality
            GROUP BY year
            ORDER BY year
        """)

    def get_poverty_vs_inequality(self) -> pd.DataFrame:
        """Get poverty vs inequality comparison for scatter plot."""
        return self.query("""
            SELECT country, region, extreme_poverty_rate, gini,
                   mean, poverty_tier, inequality_tier
            FROM country_latest
            WHERE extreme_poverty_rate IS NOT NULL AND gini IS NOT NULL
            ORDER BY extreme_poverty_rate DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest = self.get_country_latest()

        # Filter out nulls for calculations
        with_poverty = latest[latest['extreme_poverty_rate'].notna()]
        with_gini = latest[latest['gini'].notna()]

        highest_poverty = with_poverty.iloc[0] if len(with_poverty) > 0 else None
        lowest_poverty = with_poverty.iloc[-1] if len(with_poverty) > 0 else None
        highest_gini = with_gini.loc[with_gini['gini'].idxmax()] if len(with_gini) > 0 else None
        lowest_gini = with_gini.loc[with_gini['gini'].idxmin()] if len(with_gini) > 0 else None

        # Get total in extreme poverty
        total_extreme_poor = latest['extreme_poverty_count'].sum()

        return {
            "project": self.PROJECT_NAME,
            "countries": len(latest),
            "years_covered": f"{self.query('SELECT MIN(year) FROM poverty_inequality').iloc[0, 0]}-{self.query('SELECT MAX(year) FROM poverty_inequality').iloc[0, 0]}",
            "highest_poverty_country": highest_poverty['country'] if highest_poverty is not None else "N/A",
            "highest_poverty_rate": round(highest_poverty['extreme_poverty_rate'], 1) if highest_poverty is not None else 0,
            "lowest_poverty_country": lowest_poverty['country'] if lowest_poverty is not None else "N/A",
            "lowest_poverty_rate": round(lowest_poverty['extreme_poverty_rate'], 2) if lowest_poverty is not None else 0,
            "most_unequal_country": highest_gini['country'] if highest_gini is not None else "N/A",
            "highest_gini": round(highest_gini['gini'], 3) if highest_gini is not None else 0,
            "most_equal_country": lowest_gini['country'] if lowest_gini is not None else "N/A",
            "lowest_gini": round(lowest_gini['gini'], 3) if lowest_gini is not None else 0,
            "avg_extreme_poverty": round(with_poverty['extreme_poverty_rate'].mean(), 1),
            "avg_gini": round(with_gini['gini'].mean(), 3),
            "total_extreme_poor_millions": round(total_extreme_poor / 1_000_000, 0) if pd.notna(total_extreme_poor) else 0,
        }


if __name__ == "__main__":
    with PovertyInequalityDatabase() as db:
        print("Stats:", db.get_stats())
