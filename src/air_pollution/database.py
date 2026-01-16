"""
DuckDB database for Air Pollution Deaths data (Lelieveld et al. 2019).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class AirPollutionDatabase(BaseDatabase):
    """Database manager for air pollution deaths data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "air_pollution.duckdb"
    PROJECT_NAME = "Air Pollution Deaths"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating air pollution database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS air_pollution (
                entity VARCHAR,
                year INTEGER,
                deaths_all_sources DOUBLE,
                deaths_fossil_fuels DOUBLE,
                deaths_anthropogenic DOUBLE,
                yll_all_sources DOUBLE,
                yll_fossil_fuels DOUBLE,
                yll_anthropogenic DOUBLE,
                death_rate_all DOUBLE,
                death_rate_fossil DOUBLE,
                death_rate_anthropogenic DOUBLE,
                yll_rate_all DOUBLE,
                yll_rate_fossil DOUBLE,
                yll_rate_anthropogenic DOUBLE,
                share_fossil_total DOUBLE,
                share_fossil_anthropogenic DOUBLE,
                share_anthropogenic_total DOUBLE,
                region VARCHAR,
                death_rate_tier VARCHAR,
                fossil_share_tier VARCHAR,
                deaths_all_thousands DOUBLE,
                deaths_fossil_thousands DOUBLE,
                deaths_anthropogenic_thousands DOUBLE,
                yll_all_millions DOUBLE,
                yll_fossil_millions DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                total_deaths_all DOUBLE,
                total_deaths_fossil DOUBLE,
                total_deaths_anthropogenic DOUBLE,
                total_yll DOUBLE,
                avg_death_rate DOUBLE,
                avg_death_rate_fossil DOUBLE,
                avg_fossil_share DOUBLE,
                deaths_millions DOUBLE,
                yll_millions DOUBLE
            )
        """)

        # Death rate tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS death_rate_summary (
                death_rate_tier VARCHAR,
                countries INTEGER,
                avg_death_rate DOUBLE,
                min_death_rate DOUBLE,
                max_death_rate DOUBLE,
                avg_fossil_share DOUBLE,
                total_deaths DOUBLE
            )
        """)

        # Fossil share tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fossil_share_summary (
                fossil_share_tier VARCHAR,
                countries INTEGER,
                avg_fossil_share DOUBLE,
                min_fossil_share DOUBLE,
                max_fossil_share DOUBLE,
                avg_death_rate DOUBLE,
                total_fossil_deaths DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  death_rate_df: pd.DataFrame, fossil_share_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["air_pollution", "region_summary", "death_rate_summary", "fossil_share_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO air_pollution SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into air_pollution")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO death_rate_summary SELECT * FROM death_rate_df")
        logger.info(f"Loaded {len(death_rate_df)} rows into death_rate_summary")

        self.conn.execute("INSERT INTO fossil_share_summary SELECT * FROM fossil_share_df")
        logger.info(f"Loaded {len(fossil_share_df)} rows into fossil_share_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all air pollution data."""
        return self.query("SELECT * FROM air_pollution ORDER BY deaths_all_sources DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY total_deaths_all DESC")

    def get_death_rate_summary(self) -> pd.DataFrame:
        """Get death rate tier summary."""
        return self.query("""
            SELECT * FROM death_rate_summary
            ORDER BY CASE death_rate_tier
                WHEN 'Very High (150+)' THEN 1
                WHEN 'High (100-150)' THEN 2
                WHEN 'Moderate (50-100)' THEN 3
                WHEN 'Low (25-50)' THEN 4
                WHEN 'Very Low (<25)' THEN 5
                ELSE 6
            END
        """)

    def get_fossil_share_summary(self) -> pd.DataFrame:
        """Get fossil share tier summary."""
        return self.query("""
            SELECT * FROM fossil_share_summary
            ORDER BY CASE fossil_share_tier
                WHEN 'Very High (50%+)' THEN 1
                WHEN 'High (30-50%)' THEN 2
                WHEN 'Moderate (15-30%)' THEN 3
                WHEN 'Low (5-15%)' THEN 4
                WHEN 'Very Low (<5%)' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT entity FROM air_pollution ORDER BY entity")
        return result['entity'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM air_pollution
            WHERE entity = '{country}'
        """)

    def get_highest_death_rate(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest death rates."""
        return self.query(f"""
            SELECT entity, region, death_rate_all, death_rate_fossil,
                   share_fossil_total, death_rate_tier
            FROM air_pollution
            ORDER BY death_rate_all DESC
            LIMIT {limit}
        """)

    def get_lowest_death_rate(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest death rates."""
        return self.query(f"""
            SELECT entity, region, death_rate_all, death_rate_fossil,
                   share_fossil_total, death_rate_tier
            FROM air_pollution
            ORDER BY death_rate_all ASC
            LIMIT {limit}
        """)

    def get_most_deaths(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most total deaths."""
        return self.query(f"""
            SELECT entity, region, deaths_all_thousands, deaths_fossil_thousands,
                   death_rate_all, share_fossil_total
            FROM air_pollution
            ORDER BY deaths_all_sources DESC
            LIMIT {limit}
        """)

    def get_highest_fossil_share(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest fossil fuel share of deaths."""
        return self.query(f"""
            SELECT entity, region, share_fossil_total, death_rate_fossil,
                   deaths_fossil_thousands, fossil_share_tier
            FROM air_pollution
            ORDER BY share_fossil_total DESC
            LIMIT {limit}
        """)

    def get_lowest_fossil_share(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest fossil fuel share of deaths."""
        return self.query(f"""
            SELECT entity, region, share_fossil_total, death_rate_fossil,
                   deaths_fossil_thousands, fossil_share_tier
            FROM air_pollution
            ORDER BY share_fossil_total ASC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT entity, deaths_all_thousands, death_rate_all,
                   share_fossil_total, death_rate_tier
            FROM air_pollution
            WHERE region = '{region}'
            ORDER BY deaths_all_sources DESC
        """)

    def get_most_yll(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most years of life lost."""
        return self.query(f"""
            SELECT entity, region, yll_all_millions, yll_fossil_millions,
                   yll_rate_all, deaths_all_thousands
            FROM air_pollution
            ORDER BY yll_all_sources DESC
            LIMIT {limit}
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        total_deaths = self.query("SELECT SUM(deaths_all_sources) as total FROM air_pollution")['total'].iloc[0]
        total_fossil = self.query("SELECT SUM(deaths_fossil_fuels) as total FROM air_pollution")['total'].iloc[0]
        total_yll = self.query("SELECT SUM(yll_all_sources) as total FROM air_pollution")['total'].iloc[0]

        most_deaths = self.query("""
            SELECT entity, deaths_all_thousands FROM air_pollution
            ORDER BY deaths_all_sources DESC LIMIT 1
        """).iloc[0]

        highest_rate = self.query("""
            SELECT entity, death_rate_all FROM air_pollution
            ORDER BY death_rate_all DESC LIMIT 1
        """).iloc[0]

        highest_fossil_share = self.query("""
            SELECT entity, share_fossil_total FROM air_pollution
            ORDER BY share_fossil_total DESC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM air_pollution").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM air_pollution").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "total_deaths_millions": total_deaths / 1e6 if total_deaths else 0,
            "total_fossil_deaths_millions": total_fossil / 1e6 if total_fossil else 0,
            "total_yll_millions": total_yll / 1e6 if total_yll else 0,
            "most_deaths_country": most_deaths['entity'],
            "most_deaths_thousands": most_deaths['deaths_all_thousands'],
            "highest_death_rate_country": highest_rate['entity'],
            "highest_death_rate": highest_rate['death_rate_all'],
            "highest_fossil_share_country": highest_fossil_share['entity'],
            "highest_fossil_share": highest_fossil_share['share_fossil_total'],
        }


if __name__ == "__main__":
    with AirPollutionDatabase() as db:
        print("Stats:", db.get_stats())
