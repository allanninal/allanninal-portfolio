"""
DuckDB database for Suicide Rates data (IHME, 2019).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class SuicideRatesDatabase(BaseDatabase):
    """Database manager for suicide rates data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "suicide_rates.duckdb"
    PROJECT_NAME = "Suicide Rates by Sex and Age"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating suicide rates database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS suicide_rates (
                entity VARCHAR,
                year INTEGER,
                male_rate DOUBLE,
                female_rate DOUBLE,
                gender_ratio DOUBLE,
                male_15_19 DOUBLE,
                female_15_19 DOUBLE,
                both_15_19 DOUBLE,
                male_20_24 DOUBLE,
                female_20_24 DOUBLE,
                both_20_24 DOUBLE,
                male_25_29 DOUBLE,
                female_25_29 DOUBLE,
                both_25_29 DOUBLE,
                male_30_34 DOUBLE,
                female_30_34 DOUBLE,
                both_30_34 DOUBLE,
                male_35_39 DOUBLE,
                female_35_39 DOUBLE,
                both_35_39 DOUBLE,
                male_40_44 DOUBLE,
                female_40_44 DOUBLE,
                both_40_44 DOUBLE,
                male_45_49 DOUBLE,
                female_45_49 DOUBLE,
                both_45_49 DOUBLE,
                male_50_69 DOUBLE,
                female_50_69 DOUBLE,
                both_50_69 DOUBLE,
                male_70_plus DOUBLE,
                female_70_plus DOUBLE,
                both_70_plus DOUBLE,
                region VARCHAR,
                rate_tier VARCHAR,
                ratio_tier VARCHAR,
                overall_rate DOUBLE
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_male_rate DOUBLE,
                avg_female_rate DOUBLE,
                avg_gender_ratio DOUBLE,
                avg_overall_rate DOUBLE
            )
        """)

        # Age group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS age_summary (
                age_group VARCHAR,
                male_rate DOUBLE,
                female_rate DOUBLE,
                both_rate DOUBLE,
                gender_ratio DOUBLE
            )
        """)

        # Rate tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                rate_tier VARCHAR,
                countries INTEGER,
                avg_rate DOUBLE,
                min_rate DOUBLE,
                max_rate DOUBLE,
                avg_ratio DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  age_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["suicide_rates", "region_summary", "age_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO suicide_rates SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into suicide_rates")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO age_summary SELECT * FROM age_df")
        logger.info(f"Loaded {len(age_df)} rows into age_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all suicide rates data."""
        return self.query("SELECT * FROM suicide_rates ORDER BY year DESC, male_rate DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_overall_rate DESC")

    def get_age_summary(self) -> pd.DataFrame:
        """Get age group summary."""
        return self.query("""
            SELECT * FROM age_summary
            ORDER BY CASE age_group
                WHEN '15-19' THEN 1
                WHEN '20-24' THEN 2
                WHEN '25-29' THEN 3
                WHEN '30-34' THEN 4
                WHEN '35-39' THEN 5
                WHEN '40-44' THEN 6
                WHEN '45-49' THEN 7
                WHEN '50-69' THEN 8
                WHEN '70+' THEN 9
                ELSE 10
            END
        """)

    def get_tier_summary(self) -> pd.DataFrame:
        """Get rate tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE rate_tier
                WHEN 'Very High (20+)' THEN 1
                WHEN 'High (15-20)' THEN 2
                WHEN 'Moderate (10-15)' THEN 3
                WHEN 'Low (5-10)' THEN 4
                WHEN 'Very Low (<5)' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT entity FROM suicide_rates ORDER BY entity")
        return result['entity'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM suicide_rates
            WHERE entity = '{country}'
            ORDER BY year
        """)

    def get_latest_data(self) -> pd.DataFrame:
        """Get most recent year data for each country."""
        return self.query("""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.*
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.male_rate DESC
        """)

    def get_highest_male_rates(self, limit: int = 20, year: int = None) -> pd.DataFrame:
        """Get countries with highest male suicide rates."""
        year_filter = f"AND year = {year}" if year else ""
        return self.query(f"""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                WHERE 1=1 {year_filter}
                GROUP BY entity
            )
            SELECT s.entity, s.region, s.year, s.male_rate, s.female_rate,
                   s.gender_ratio, s.rate_tier
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.male_rate DESC
            LIMIT {limit}
        """)

    def get_highest_female_rates(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest female suicide rates."""
        return self.query(f"""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.region, s.year, s.female_rate, s.male_rate,
                   s.gender_ratio, s.rate_tier
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.female_rate DESC
            LIMIT {limit}
        """)

    def get_highest_gender_ratio(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest male:female ratio."""
        return self.query(f"""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.region, s.year, s.gender_ratio,
                   s.male_rate, s.female_rate, s.ratio_tier
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            WHERE s.gender_ratio IS NOT NULL
            ORDER BY s.gender_ratio DESC
            LIMIT {limit}
        """)

    def get_lowest_gender_ratio(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest male:female ratio."""
        return self.query(f"""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.region, s.year, s.gender_ratio,
                   s.male_rate, s.female_rate, s.ratio_tier
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            WHERE s.gender_ratio IS NOT NULL AND s.gender_ratio > 0
            ORDER BY s.gender_ratio ASC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get latest data for countries in a region."""
        return self.query(f"""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                WHERE region = '{region}'
                GROUP BY entity
            )
            SELECT s.entity, s.year, s.male_rate, s.female_rate,
                   s.gender_ratio, s.rate_tier
            FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.male_rate DESC
        """)

    def get_global_trend(self) -> pd.DataFrame:
        """Get global average trend over years."""
        return self.query("""
            SELECT year,
                   AVG(male_rate) as avg_male_rate,
                   AVG(female_rate) as avg_female_rate,
                   AVG(overall_rate) as avg_overall_rate,
                   AVG(gender_ratio) as avg_gender_ratio
            FROM suicide_rates
            GROUP BY year
            ORDER BY year
        """)

    def get_age_profile_by_country(self, country: str) -> pd.DataFrame:
        """Get age-specific rates for a country (latest year)."""
        return self.query(f"""
            WITH latest AS (
                SELECT MAX(year) as max_year
                FROM suicide_rates
                WHERE entity = '{country}'
            )
            SELECT
                '15-19' as age_group, male_15_19 as male_rate, female_15_19 as female_rate, both_15_19 as both_rate
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '20-24', male_20_24, female_20_24, both_20_24
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '25-29', male_25_29, female_25_29, both_25_29
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '30-34', male_30_34, female_30_34, both_30_34
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '35-39', male_35_39, female_35_39, both_35_39
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '40-44', male_40_44, female_40_44, both_40_44
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '45-49', male_45_49, female_45_49, both_45_49
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '50-69', male_50_69, female_50_69, both_50_69
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
            UNION ALL
            SELECT
                '70+', male_70_plus, female_70_plus, both_70_plus
            FROM suicide_rates, latest
            WHERE entity = '{country}' AND year = latest.max_year
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest_data = self.get_latest_data()

        highest_male = self.query("""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.male_rate FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.male_rate DESC LIMIT 1
        """).iloc[0]

        highest_female = self.query("""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.female_rate FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            ORDER BY s.female_rate DESC LIMIT 1
        """).iloc[0]

        highest_ratio = self.query("""
            WITH latest AS (
                SELECT entity, MAX(year) as max_year
                FROM suicide_rates
                GROUP BY entity
            )
            SELECT s.entity, s.gender_ratio FROM suicide_rates s
            JOIN latest l ON s.entity = l.entity AND s.year = l.max_year
            WHERE s.gender_ratio IS NOT NULL
            ORDER BY s.gender_ratio DESC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM suicide_rates").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM suicide_rates").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "year_min": self.conn.execute("SELECT MIN(year) FROM suicide_rates").fetchone()[0],
            "year_max": self.conn.execute("SELECT MAX(year) FROM suicide_rates").fetchone()[0],
            "highest_rate_country": highest_male['entity'],
            "highest_rate": highest_male['male_rate'],
            "highest_female_country": highest_female['entity'],
            "highest_female_rate": highest_female['female_rate'],
            "highest_ratio_country": highest_ratio['entity'],
            "highest_ratio": highest_ratio['gender_ratio'],
            "avg_male_rate": latest_data['male_rate'].mean(),
            "avg_female_rate": latest_data['female_rate'].mean(),
            "avg_gender_ratio": latest_data['gender_ratio'].mean(),
        }


if __name__ == "__main__":
    with SuicideRatesDatabase() as db:
        print("Stats:", db.get_stats())
