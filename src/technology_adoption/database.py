"""
DuckDB database for US Technology Adoption data.
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Optional, List

from src.shared.base_database import BaseDatabase


class TechnologyAdoptionDatabase(BaseDatabase):
    """Database manager for technology adoption data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "technology_adoption.duckdb"
    PROJECT_NAME = "Technology Adoption"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating technology adoption database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS technology_adoption (
                technology VARCHAR,
                year INTEGER,
                adoption_pct DOUBLE,
                category VARCHAR,
                decade VARCHAR,
                adoption_tier VARCHAR
            )
        """)

        # Technology summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS technology_summary (
                technology VARCHAR,
                category VARCHAR,
                first_year INTEGER,
                last_year INTEGER,
                max_adoption DOUBLE,
                current_adoption DOUBLE,
                years_tracked INTEGER,
                years_to_50_pct INTEGER,
                peak_year INTEGER
            )
        """)

        # Category summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS category_summary (
                category VARCHAR,
                technologies INTEGER,
                avg_max_adoption DOUBLE,
                avg_years_to_peak DOUBLE,
                oldest_tech_year INTEGER,
                newest_tech_year INTEGER
            )
        """)

        # Decade summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decade_summary (
                decade VARCHAR,
                avg_adoption DOUBLE,
                technologies_tracked INTEGER,
                new_technologies INTEGER
            )
        """)

        # Useful views
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_technology_timeline AS
            SELECT technology, year, adoption_pct, category
            FROM technology_adoption
            ORDER BY technology, year
        """)

        self.conn.execute("""
            CREATE OR REPLACE VIEW v_adoption_leaders AS
            SELECT technology, category, max_adoption, years_to_50_pct, first_year
            FROM technology_summary
            WHERE max_adoption >= 50
            ORDER BY years_to_50_pct ASC NULLS LAST
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, tech_summary_df: pd.DataFrame,
                  category_summary_df: pd.DataFrame, decade_summary_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        # Clear existing
        for table in ["technology_adoption", "technology_summary", "category_summary", "decade_summary"]:
            self.conn.execute(f"DELETE FROM {table}")

        # Load each table
        self.conn.execute("INSERT INTO technology_adoption SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into technology_adoption")

        self.conn.execute("INSERT INTO technology_summary SELECT * FROM tech_summary_df")
        logger.info(f"Loaded {len(tech_summary_df)} rows into technology_summary")

        self.conn.execute("INSERT INTO category_summary SELECT * FROM category_summary_df")
        logger.info(f"Loaded {len(category_summary_df)} rows into category_summary")

        self.conn.execute("INSERT INTO decade_summary SELECT * FROM decade_summary_df")
        logger.info(f"Loaded {len(decade_summary_df)} rows into decade_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all technology adoption data."""
        return self.query("SELECT * FROM technology_adoption ORDER BY technology, year")

    def get_technology_summary(self) -> pd.DataFrame:
        """Get technology summary."""
        return self.query("SELECT * FROM technology_summary ORDER BY first_year")

    def get_category_summary(self) -> pd.DataFrame:
        """Get category summary."""
        return self.query("SELECT * FROM category_summary ORDER BY technologies DESC")

    def get_decade_summary(self) -> pd.DataFrame:
        """Get decade summary."""
        return self.query("SELECT * FROM decade_summary ORDER BY decade")

    def get_technology_data(self, technology: str) -> pd.DataFrame:
        """Get data for a specific technology."""
        return self.query(f"""
            SELECT year, adoption_pct
            FROM technology_adoption
            WHERE technology = '{technology}'
            ORDER BY year
        """)

    def get_technologies_by_category(self, category: str) -> List[str]:
        """Get list of technologies in a category."""
        result = self.query(f"""
            SELECT DISTINCT technology
            FROM technology_adoption
            WHERE category = '{category}'
            ORDER BY technology
        """)
        return result['technology'].tolist()

    def get_technologies_list(self) -> List[str]:
        """Get list of all technologies."""
        result = self.query("""
            SELECT DISTINCT technology
            FROM technology_adoption
            ORDER BY technology
        """)
        return result['technology'].tolist()

    def get_categories_list(self) -> List[str]:
        """Get list of all categories."""
        result = self.query("""
            SELECT DISTINCT category
            FROM technology_adoption
            ORDER BY category
        """)
        return result['category'].tolist()

    def get_fastest_adopters(self, limit: int = 10) -> pd.DataFrame:
        """Get technologies with fastest adoption to 50%."""
        return self.query(f"""
            SELECT technology, category, first_year, years_to_50_pct, max_adoption
            FROM technology_summary
            WHERE years_to_50_pct IS NOT NULL
            ORDER BY years_to_50_pct ASC
            LIMIT {limit}
        """)

    def get_adoption_by_year(self, year: int) -> pd.DataFrame:
        """Get all technology adoption for a specific year."""
        return self.query(f"""
            SELECT technology, category, adoption_pct
            FROM technology_adoption
            WHERE year = {year}
            ORDER BY adoption_pct DESC
        """)

    def get_year_range(self) -> tuple:
        """Get min and max years in data."""
        result = self.query("""
            SELECT MIN(year) as min_year, MAX(year) as max_year
            FROM technology_adoption
        """)
        return (result['min_year'].iloc[0], result['max_year'].iloc[0])

    def get_stats(self) -> dict:
        """Get database statistics."""
        year_range = self.get_year_range()
        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM technology_adoption").fetchone()[0],
            "technologies": self.conn.execute("SELECT COUNT(DISTINCT technology) FROM technology_adoption").fetchone()[0],
            "categories": self.conn.execute("SELECT COUNT(*) FROM category_summary").fetchone()[0],
            "year_range": year_range,
            "years_covered": year_range[1] - year_range[0] + 1 if year_range[0] else 0,
        }


if __name__ == "__main__":
    with TechnologyAdoptionDatabase() as db:
        print("Stats:", db.get_stats())
