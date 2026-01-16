"""
DuckDB database for Education Quality data (Altinok, Angrist, and Patrinos 2018).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class EducationQualityDatabase(BaseDatabase):
    """Database manager for education quality data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "education_quality.duckdb"
    PROJECT_NAME = "Education Quality"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating education quality database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS education_quality (
                entity VARCHAR,
                country_base VARCHAR,
                year INTEGER,
                era VARCHAR,
                region VARCHAR,
                avg_score DOUBLE,
                pct_minimum DOUBLE,
                pct_intermediate DOUBLE,
                pct_advanced DOUBLE,
                performance_tier VARCHAR,
                gap_from_best DOUBLE,
                is_country BOOLEAN
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                entity VARCHAR,
                region VARCHAR,
                earliest_year INTEGER,
                latest_year INTEGER,
                earliest_score DOUBLE,
                latest_score DOUBLE,
                score_change DOUBLE,
                latest_pct_minimum DOUBLE,
                latest_pct_advanced DOUBLE,
                data_points INTEGER,
                performance_tier VARCHAR
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_score DOUBLE,
                min_score DOUBLE,
                max_score DOUBLE,
                std_score DOUBLE,
                avg_pct_minimum DOUBLE,
                avg_pct_advanced DOUBLE
            )
        """)

        # Era summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS era_summary (
                era VARCHAR,
                countries_tested INTEGER,
                avg_score DOUBLE,
                min_score DOUBLE,
                max_score DOUBLE,
                avg_pct_minimum DOUBLE,
                avg_pct_advanced DOUBLE
            )
        """)

        # Tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tier_summary (
                performance_tier VARCHAR,
                countries INTEGER,
                avg_score DOUBLE,
                min_score DOUBLE,
                max_score DOUBLE,
                avg_pct_minimum DOUBLE,
                avg_pct_advanced DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, era_df: pd.DataFrame, tier_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["education_quality", "country_summary", "region_summary", "era_summary", "tier_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO education_quality SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into education_quality")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO era_summary SELECT * FROM era_df")
        logger.info(f"Loaded {len(era_df)} rows into era_summary")

        self.conn.execute("INSERT INTO tier_summary SELECT * FROM tier_df")
        logger.info(f"Loaded {len(tier_df)} rows into tier_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all education quality data."""
        return self.query("SELECT * FROM education_quality ORDER BY entity, year")

    def get_country_data_only(self) -> pd.DataFrame:
        """Get only country-level data (no sub-national regions)."""
        return self.query("SELECT * FROM education_quality WHERE is_country = true ORDER BY entity, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM country_summary ORDER BY latest_score DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_score DESC")

    def get_era_summary(self) -> pd.DataFrame:
        """Get era trends."""
        return self.query("""
            SELECT * FROM era_summary
            ORDER BY CASE era
                WHEN '1965-1979' THEN 1
                WHEN '1980-1989' THEN 2
                WHEN '1990-1999' THEN 3
                WHEN '2000-2009' THEN 4
                WHEN '2010-2015' THEN 5
            END
        """)

    def get_tier_summary(self) -> pd.DataFrame:
        """Get performance tier summary."""
        return self.query("""
            SELECT * FROM tier_summary
            ORDER BY CASE performance_tier
                WHEN 'High (525+)' THEN 1
                WHEN 'Upper-Middle (475-525)' THEN 2
                WHEN 'Middle (425-475)' THEN 3
                WHEN 'Lower-Middle (375-425)' THEN 4
                WHEN 'Low (<375)' THEN 5
                ELSE 6
            END
        """)

    def get_entities_list(self) -> List[str]:
        """Get list of all entities."""
        result = self.query("SELECT DISTINCT entity FROM education_quality ORDER BY entity")
        return result['entity'].tolist()

    def get_countries_list(self) -> List[str]:
        """Get list of countries only (no sub-national)."""
        result = self.query("SELECT DISTINCT entity FROM education_quality WHERE is_country = true ORDER BY entity")
        return result['entity'].tolist()

    def get_entity_data(self, entity: str) -> pd.DataFrame:
        """Get data for a specific entity."""
        return self.query(f"""
            SELECT * FROM education_quality
            WHERE entity = '{entity}'
            ORDER BY year
        """)

    def get_top_countries(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest scores."""
        return self.query(f"""
            SELECT entity, region, latest_score, score_change, latest_pct_advanced, performance_tier
            FROM country_summary
            WHERE latest_score IS NOT NULL
            ORDER BY latest_score DESC
            LIMIT {limit}
        """)

    def get_bottom_countries(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest scores."""
        return self.query(f"""
            SELECT entity, region, latest_score, score_change, latest_pct_minimum, performance_tier
            FROM country_summary
            WHERE latest_score IS NOT NULL
            ORDER BY latest_score ASC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with largest score improvements."""
        return self.query(f"""
            SELECT entity, region, earliest_score, latest_score, score_change, earliest_year, latest_year
            FROM country_summary
            WHERE score_change IS NOT NULL AND data_points > 1
            ORDER BY score_change DESC
            LIMIT {limit}
        """)

    def get_most_declined(self, limit: int = 15) -> pd.DataFrame:
        """Get countries with largest score declines."""
        return self.query(f"""
            SELECT entity, region, earliest_score, latest_score, score_change, earliest_year, latest_year
            FROM country_summary
            WHERE score_change IS NOT NULL AND data_points > 1
            ORDER BY score_change ASC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT entity, latest_score, score_change, latest_pct_minimum, latest_pct_advanced, performance_tier
            FROM country_summary
            WHERE region = '{region}'
            ORDER BY latest_score DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        global_avg = self.query("""
            SELECT AVG(avg_score) as avg FROM education_quality
            WHERE is_country = true
        """)['avg'].iloc[0]

        best = self.query("""
            SELECT entity, latest_score FROM country_summary
            ORDER BY latest_score DESC LIMIT 1
        """).iloc[0]

        years = self.query("SELECT MIN(year) as min_y, MAX(year) as max_y FROM education_quality").iloc[0].tolist()

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM education_quality").fetchone()[0],
            "entities": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM education_quality").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM education_quality WHERE is_country = true").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": years,
            "global_avg": round(global_avg, 1) if global_avg else 0,
            "best_entity": best['entity'],
            "best_score": round(best['latest_score'], 1),
        }


if __name__ == "__main__":
    with EducationQualityDatabase() as db:
        print("Stats:", db.get_stats())
