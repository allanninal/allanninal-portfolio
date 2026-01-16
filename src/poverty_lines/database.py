"""
DuckDB database for National Poverty Lines (Jolliffe et al., 2022).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class PovertyLinesDatabase(BaseDatabase):
    """Database manager for national poverty lines data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "poverty_lines.duckdb"
    PROJECT_NAME = "National Poverty Lines"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating poverty lines database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS poverty_lines (
                country VARCHAR,
                year INTEGER,
                income_group VARCHAR,
                poverty_line DOUBLE,
                region VARCHAR,
                poverty_tier VARCHAR,
                poverty_line_rounded DOUBLE
            )
        """)

        # Income group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS income_summary (
                income_group VARCHAR,
                countries INTEGER,
                avg_poverty_line DOUBLE,
                min_poverty_line DOUBLE,
                max_poverty_line DOUBLE,
                median_poverty_line DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_poverty_line DOUBLE,
                min_poverty_line DOUBLE,
                max_poverty_line DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, income_df: pd.DataFrame,
                  region_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["poverty_lines", "income_summary", "region_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO poverty_lines SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into poverty_lines")

        self.conn.execute("INSERT INTO income_summary SELECT * FROM income_df")
        logger.info(f"Loaded {len(income_df)} rows into income_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all poverty lines data."""
        return self.query("SELECT * FROM poverty_lines ORDER BY poverty_line ASC")

    def get_income_summary(self) -> pd.DataFrame:
        """Get income group summary."""
        return self.query("""
            SELECT * FROM income_summary
            ORDER BY CASE income_group
                WHEN 'Low income' THEN 1
                WHEN 'Lower middle income' THEN 2
                WHEN 'Upper middle income' THEN 3
                WHEN 'High income' THEN 4
                ELSE 5
            END
        """)

    def get_region_summary(self) -> pd.DataFrame:
        """Get region summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_poverty_line ASC")

    def get_lowest_poverty_lines(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest poverty lines."""
        return self.query(f"""
            SELECT country, region, income_group, poverty_line_rounded, poverty_tier
            FROM poverty_lines
            ORDER BY poverty_line ASC
            LIMIT {limit}
        """)

    def get_highest_poverty_lines(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest poverty lines."""
        return self.query(f"""
            SELECT country, region, income_group, poverty_line_rounded, poverty_tier
            FROM poverty_lines
            ORDER BY poverty_line DESC
            LIMIT {limit}
        """)

    def get_by_income_group(self, income_group: str) -> pd.DataFrame:
        """Get countries by income group."""
        return self.query(f"""
            SELECT country, region, poverty_line_rounded, poverty_tier
            FROM poverty_lines
            WHERE income_group = '{income_group}'
            ORDER BY poverty_line ASC
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT country, income_group, poverty_line_rounded, poverty_tier
            FROM poverty_lines
            WHERE region = '{region}'
            ORDER BY poverty_line ASC
        """)

    def get_by_tier(self, tier: str) -> pd.DataFrame:
        """Get countries by poverty tier."""
        return self.query(f"""
            SELECT country, region, income_group, poverty_line_rounded
            FROM poverty_lines
            WHERE poverty_tier = '{tier}'
            ORDER BY poverty_line ASC
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM poverty_lines
            WHERE country = '{country}'
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM poverty_lines ORDER BY country")
        return result['country'].tolist()

    def get_regions_list(self):
        """Get list of all regions."""
        result = self.query("SELECT DISTINCT region FROM poverty_lines ORDER BY region")
        return result['region'].tolist()

    def get_income_groups_list(self):
        """Get list of all income groups."""
        result = self.query("SELECT DISTINCT income_group FROM poverty_lines ORDER BY income_group")
        return result['income_group'].tolist()

    def get_comparison_to_ipl(self) -> pd.DataFrame:
        """Compare national lines to International Poverty Line ($2.15)."""
        return self.query("""
            SELECT country, region, income_group, poverty_line_rounded,
                   ROUND(poverty_line / 2.15, 1) as multiple_of_ipl,
                   CASE
                       WHEN poverty_line < 2.15 THEN 'Below IPL'
                       WHEN poverty_line < 4.30 THEN '1-2x IPL'
                       WHEN poverty_line < 10.75 THEN '2-5x IPL'
                       WHEN poverty_line < 21.50 THEN '5-10x IPL'
                       ELSE '>10x IPL'
                   END as ipl_category
            FROM poverty_lines
            ORDER BY poverty_line ASC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        data = self.get_full_data()

        lowest = data.iloc[0]
        highest = data.iloc[-1]

        return {
            "project": self.PROJECT_NAME,
            "countries": len(data),
            "lowest_line_country": lowest['country'],
            "lowest_line": lowest['poverty_line_rounded'],
            "highest_line_country": highest['country'],
            "highest_line": highest['poverty_line_rounded'],
            "avg_poverty_line": data['poverty_line'].mean().round(2),
            "median_poverty_line": data['poverty_line'].median().round(2),
            "ratio_highest_lowest": (highest['poverty_line'] / lowest['poverty_line']).round(1),
            "income_groups": data['income_group'].nunique(),
            "international_poverty_line": 2.15,
        }


if __name__ == "__main__":
    with PovertyLinesDatabase() as db:
        print("Stats:", db.get_stats())
