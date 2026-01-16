"""
DuckDB database for Tree Density data (Crowther et al. 2015).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class TreeDensityDatabase(BaseDatabase):
    """Database manager for tree density data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "tree_density.duckdb"
    PROJECT_NAME = "Tree Density"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating tree density database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tree_density (
                entity VARCHAR,
                year INTEGER,
                region VARCHAR,
                num_trees DOUBLE,
                trees_billions DOUBLE,
                pct_world_trees DOUBLE,
                trees_per_km2 DOUBLE,
                trees_per_capita DOUBLE,
                density_tier VARCHAR,
                per_capita_tier VARCHAR
            )
        """)

        # Region summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                total_trees DOUBLE,
                avg_density DOUBLE,
                min_density DOUBLE,
                max_density DOUBLE,
                avg_per_capita DOUBLE,
                min_per_capita DOUBLE,
                max_per_capita DOUBLE,
                trees_billions DOUBLE
            )
        """)

        # Density tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS density_summary (
                density_tier VARCHAR,
                countries INTEGER,
                avg_density DOUBLE,
                min_density DOUBLE,
                max_density DOUBLE,
                avg_per_capita DOUBLE
            )
        """)

        # Per capita tier summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS per_capita_summary (
                per_capita_tier VARCHAR,
                countries INTEGER,
                avg_per_capita DOUBLE,
                min_per_capita DOUBLE,
                max_per_capita DOUBLE,
                avg_density DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, region_df: pd.DataFrame,
                  density_df: pd.DataFrame, per_capita_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["tree_density", "region_summary", "density_summary", "per_capita_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO tree_density SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into tree_density")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO density_summary SELECT * FROM density_df")
        logger.info(f"Loaded {len(density_df)} rows into density_summary")

        self.conn.execute("INSERT INTO per_capita_summary SELECT * FROM per_capita_df")
        logger.info(f"Loaded {len(per_capita_df)} rows into per_capita_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all tree density data."""
        return self.query("SELECT * FROM tree_density ORDER BY num_trees DESC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY total_trees DESC")

    def get_density_summary(self) -> pd.DataFrame:
        """Get density tier summary."""
        return self.query("""
            SELECT * FROM density_summary
            ORDER BY CASE density_tier
                WHEN 'Very High (50k+/km²)' THEN 1
                WHEN 'High (30-50k/km²)' THEN 2
                WHEN 'Moderate (15-30k/km²)' THEN 3
                WHEN 'Low (5-15k/km²)' THEN 4
                WHEN 'Very Low (<5k/km²)' THEN 5
                ELSE 6
            END
        """)

    def get_per_capita_summary(self) -> pd.DataFrame:
        """Get per capita tier summary."""
        return self.query("""
            SELECT * FROM per_capita_summary
            ORDER BY CASE per_capita_tier
                WHEN 'Very High (1000+)' THEN 1
                WHEN 'High (200-1000)' THEN 2
                WHEN 'Moderate (50-200)' THEN 3
                WHEN 'Low (10-50)' THEN 4
                WHEN 'Very Low (<10)' THEN 5
                ELSE 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT entity FROM tree_density ORDER BY entity")
        return result['entity'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM tree_density
            WHERE entity = '{country}'
        """)

    def get_most_trees(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most trees."""
        return self.query(f"""
            SELECT entity, region, trees_billions, pct_world_trees, trees_per_km2, trees_per_capita
            FROM tree_density
            ORDER BY num_trees DESC
            LIMIT {limit}
        """)

    def get_highest_density(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with highest tree density."""
        return self.query(f"""
            SELECT entity, region, trees_per_km2, trees_per_capita, density_tier
            FROM tree_density
            ORDER BY trees_per_km2 DESC
            LIMIT {limit}
        """)

    def get_lowest_density(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with lowest tree density."""
        return self.query(f"""
            SELECT entity, region, trees_per_km2, trees_per_capita, density_tier
            FROM tree_density
            ORDER BY trees_per_km2 ASC
            LIMIT {limit}
        """)

    def get_most_per_capita(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with most trees per capita."""
        return self.query(f"""
            SELECT entity, region, trees_per_capita, trees_per_km2, per_capita_tier
            FROM tree_density
            ORDER BY trees_per_capita DESC
            LIMIT {limit}
        """)

    def get_least_per_capita(self, limit: int = 20) -> pd.DataFrame:
        """Get countries with fewest trees per capita."""
        return self.query(f"""
            SELECT entity, region, trees_per_capita, trees_per_km2, per_capita_tier
            FROM tree_density
            ORDER BY trees_per_capita ASC
            LIMIT {limit}
        """)

    def get_by_region(self, region: str) -> pd.DataFrame:
        """Get countries by region."""
        return self.query(f"""
            SELECT entity, trees_billions, trees_per_km2, trees_per_capita, density_tier
            FROM tree_density
            WHERE region = '{region}'
            ORDER BY num_trees DESC
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        total_trees = self.query("SELECT SUM(num_trees) as total FROM tree_density")['total'].iloc[0]

        most_trees = self.query("""
            SELECT entity, trees_billions FROM tree_density
            ORDER BY num_trees DESC LIMIT 1
        """).iloc[0]

        highest_density = self.query("""
            SELECT entity, trees_per_km2 FROM tree_density
            ORDER BY trees_per_km2 DESC LIMIT 1
        """).iloc[0]

        most_per_capita = self.query("""
            SELECT entity, trees_per_capita FROM tree_density
            ORDER BY trees_per_capita DESC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM tree_density").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT entity) FROM tree_density").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "total_trees_trillion": total_trees / 1e12 if total_trees else 0,
            "most_trees_country": most_trees['entity'],
            "most_trees_billions": most_trees['trees_billions'],
            "highest_density_country": highest_density['entity'],
            "highest_density": highest_density['trees_per_km2'],
            "most_per_capita_country": most_per_capita['entity'],
            "most_per_capita": most_per_capita['trees_per_capita'],
        }


if __name__ == "__main__":
    with TreeDensityDatabase() as db:
        print("Stats:", db.get_stats())
