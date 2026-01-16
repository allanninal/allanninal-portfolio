"""
DuckDB database for Food Affordability data (World Bank/FAO).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class FoodAffordabilityDatabase(BaseDatabase):
    """Database manager for food affordability data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "food_affordability.duckdb"
    PROJECT_NAME = "Food Affordability"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating food affordability database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS food_affordability (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                income_group VARCHAR,
                cost_healthy_diet DOUBLE,
                cost_nutrient_diet DOUBLE,
                cost_energy_diet DOUBLE,
                healthy_unaffordable_share DOUBLE,
                healthy_unaffordable_number DOUBLE,
                nutrient_unaffordable_share DOUBLE,
                nutrient_unaffordable_number DOUBLE,
                energy_unaffordable_share DOUBLE,
                energy_unaffordable_number DOUBLE,
                cost_staples DOUBLE,
                cost_vegetables DOUBLE,
                cost_fruits DOUBLE,
                cost_legumes DOUBLE,
                cost_animal DOUBLE,
                cost_oils DOUBLE,
                affordability_tier VARCHAR
            )
        """)

        # Country summary (latest year)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                region VARCHAR,
                income_group VARCHAR,
                cost_healthy_diet DOUBLE,
                healthy_unaffordable_share DOUBLE,
                healthy_unaffordable_number DOUBLE,
                affordability_tier VARCHAR,
                rank_by_cost INTEGER,
                rank_by_unaffordability INTEGER
            )
        """)

        # Regional summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_cost_healthy DOUBLE,
                avg_unaffordable_share DOUBLE,
                total_unaffordable_millions DOUBLE,
                min_cost DOUBLE,
                max_cost DOUBLE
            )
        """)

        # Income group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS income_summary (
                income_group VARCHAR,
                countries INTEGER,
                avg_cost_healthy DOUBLE,
                avg_unaffordable_share DOUBLE,
                total_unaffordable_millions DOUBLE
            )
        """)

        # Diet type comparison
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS diet_comparison (
                country VARCHAR,
                region VARCHAR,
                cost_healthy DOUBLE,
                cost_nutrient DOUBLE,
                cost_energy DOUBLE,
                healthy_vs_energy_ratio DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, income_df: pd.DataFrame,
                  diet_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["food_affordability", "country_summary", "region_summary",
                  "income_summary", "diet_comparison"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO food_affordability SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into food_affordability")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO income_summary SELECT * FROM income_df")
        logger.info(f"Loaded {len(income_df)} rows into income_summary")

        self.conn.execute("INSERT INTO diet_comparison SELECT * FROM diet_df")
        logger.info(f"Loaded {len(diet_df)} rows into diet_comparison")

    def get_full_data(self) -> pd.DataFrame:
        """Get all food affordability data."""
        return self.query("SELECT * FROM food_affordability ORDER BY country, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary (latest year)."""
        return self.query("SELECT * FROM country_summary ORDER BY rank_by_cost")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_unaffordable_share DESC")

    def get_income_summary(self) -> pd.DataFrame:
        """Get income group summary."""
        return self.query("""
            SELECT * FROM income_summary
            ORDER BY CASE income_group
                WHEN 'Low income' THEN 1
                WHEN 'Lower middle income' THEN 2
                WHEN 'Upper middle income' THEN 3
                WHEN 'High income' THEN 4
            END
        """)

    def get_diet_comparison(self) -> pd.DataFrame:
        """Get diet type cost comparison."""
        return self.query("SELECT * FROM diet_comparison ORDER BY healthy_vs_energy_ratio DESC")

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM food_affordability ORDER BY country")
        return result['country'].tolist()

    def get_regions_list(self) -> List[str]:
        """Get list of all regions."""
        result = self.query("SELECT DISTINCT region FROM food_affordability WHERE region IS NOT NULL ORDER BY region")
        return result['region'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM food_affordability
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_most_affordable(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with most affordable healthy diets."""
        return self.query(f"""
            SELECT country, region, cost_healthy_diet, healthy_unaffordable_share
            FROM country_summary
            WHERE cost_healthy_diet IS NOT NULL
            ORDER BY cost_healthy_diet ASC
            LIMIT {limit}
        """)

    def get_least_affordable(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with least affordable healthy diets."""
        return self.query(f"""
            SELECT country, region, cost_healthy_diet, healthy_unaffordable_share
            FROM country_summary
            WHERE cost_healthy_diet IS NOT NULL
            ORDER BY cost_healthy_diet DESC
            LIMIT {limit}
        """)

    def get_highest_unaffordability(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with highest share unable to afford healthy diet."""
        return self.query(f"""
            SELECT country, region, healthy_unaffordable_share, cost_healthy_diet
            FROM country_summary
            WHERE healthy_unaffordable_share IS NOT NULL
            ORDER BY healthy_unaffordable_share DESC
            LIMIT {limit}
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        total_unaffordable = self.query("""
            SELECT SUM(healthy_unaffordable_number) as total
            FROM country_summary
        """)['total'].iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM food_affordability").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT country) FROM food_affordability").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": self.query("SELECT MIN(year) as min_y, MAX(year) as max_y FROM food_affordability").iloc[0].tolist(),
            "total_unaffordable_billions": round(total_unaffordable / 1000, 2) if total_unaffordable else 0,
        }


if __name__ == "__main__":
    with FoodAffordabilityDatabase() as db:
        print("Stats:", db.get_stats())
