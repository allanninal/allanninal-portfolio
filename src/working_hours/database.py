"""
DuckDB database for Working Hours data (Huberman & Minns 2007).
"""

import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List

from src.shared.base_database import BaseDatabase


class WorkingHoursDatabase(BaseDatabase):
    """Database manager for working hours data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "working_hours.duckdb"
    PROJECT_NAME = "Working Hours"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating working hours database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS working_hours (
                country VARCHAR,
                year INTEGER,
                region VARCHAR,
                era VARCHAR,
                weekly_hours DOUBLE,
                annual_hours DOUBLE,
                weeks_worked DOUBLE,
                vacation_days DOUBLE,
                hours_category VARCHAR,
                daily_hours DOUBLE
            )
        """)

        # Country summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS country_summary (
                country VARCHAR,
                region VARCHAR,
                latest_year INTEGER,
                latest_weekly_hours DOUBLE,
                latest_annual_hours INTEGER,
                earliest_year INTEGER,
                earliest_weekly_hours DOUBLE,
                weekly_change DOUBLE,
                annual_change INTEGER,
                latest_vacation_days INTEGER,
                vacation_change INTEGER,
                data_points INTEGER,
                hours_category VARCHAR
            )
        """)

        # Regional summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS region_summary (
                region VARCHAR,
                countries INTEGER,
                avg_weekly DOUBLE,
                min_weekly DOUBLE,
                max_weekly DOUBLE,
                avg_annual DOUBLE,
                avg_vacation DOUBLE
            )
        """)

        # Era summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS era_summary (
                era VARCHAR,
                avg_weekly DOUBLE,
                min_weekly DOUBLE,
                max_weekly DOUBLE,
                avg_annual DOUBLE,
                avg_vacation DOUBLE,
                countries_with_data INTEGER
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, country_df: pd.DataFrame,
                  region_df: pd.DataFrame, era_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["working_hours", "country_summary", "region_summary", "era_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO working_hours SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into working_hours")

        self.conn.execute("INSERT INTO country_summary SELECT * FROM country_df")
        logger.info(f"Loaded {len(country_df)} rows into country_summary")

        self.conn.execute("INSERT INTO region_summary SELECT * FROM region_df")
        logger.info(f"Loaded {len(region_df)} rows into region_summary")

        self.conn.execute("INSERT INTO era_summary SELECT * FROM era_df")
        logger.info(f"Loaded {len(era_df)} rows into era_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all working hours data."""
        return self.query("SELECT * FROM working_hours ORDER BY country, year")

    def get_country_summary(self) -> pd.DataFrame:
        """Get country summary."""
        return self.query("SELECT * FROM country_summary ORDER BY latest_weekly_hours ASC")

    def get_region_summary(self) -> pd.DataFrame:
        """Get regional summary."""
        return self.query("SELECT * FROM region_summary ORDER BY avg_weekly ASC")

    def get_era_summary(self) -> pd.DataFrame:
        """Get era trends."""
        return self.query("""
            SELECT * FROM era_summary
            ORDER BY CASE era
                WHEN 'Pre-1900' THEN 1
                WHEN 'Pre-WWI' THEN 2
                WHEN 'Interwar' THEN 3
                WHEN 'WWII Era' THEN 4
                WHEN 'Post-War' THEN 5
                WHEN 'Modern' THEN 6
            END
        """)

    def get_countries_list(self) -> List[str]:
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM working_hours ORDER BY country")
        return result['country'].tolist()

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM working_hours
            WHERE country = '{country}'
            ORDER BY year
        """)

    def get_shortest_week(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with shortest work weeks (most leisure)."""
        return self.query(f"""
            SELECT country, region, latest_weekly_hours, weekly_change, latest_vacation_days
            FROM country_summary
            WHERE latest_weekly_hours IS NOT NULL
            ORDER BY latest_weekly_hours ASC
            LIMIT {limit}
        """)

    def get_longest_week(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with longest work weeks."""
        return self.query(f"""
            SELECT country, region, latest_weekly_hours, weekly_change
            FROM country_summary
            WHERE latest_weekly_hours IS NOT NULL
            ORDER BY latest_weekly_hours DESC
            LIMIT {limit}
        """)

    def get_most_improved(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with largest reduction in work hours."""
        return self.query(f"""
            SELECT country, region, earliest_weekly_hours, latest_weekly_hours, weekly_change
            FROM country_summary
            WHERE weekly_change IS NOT NULL
            ORDER BY weekly_change ASC
            LIMIT {limit}
        """)

    def get_most_vacation(self, limit: int = 10) -> pd.DataFrame:
        """Get countries with most vacation days."""
        return self.query(f"""
            SELECT country, region, latest_vacation_days, vacation_change
            FROM country_summary
            WHERE latest_vacation_days IS NOT NULL
            ORDER BY latest_vacation_days DESC
            LIMIT {limit}
        """)

    def get_stats(self) -> dict:
        """Get database statistics."""
        latest_avg = self.query("""
            SELECT AVG(latest_weekly_hours) as avg FROM country_summary
            WHERE latest_weekly_hours IS NOT NULL
        """)['avg'].iloc[0]

        shortest = self.query("""
            SELECT country, latest_weekly_hours FROM country_summary
            WHERE latest_weekly_hours IS NOT NULL
            ORDER BY latest_weekly_hours ASC LIMIT 1
        """).iloc[0]

        return {
            "project": self.PROJECT_NAME,
            "total_records": self.conn.execute("SELECT COUNT(*) FROM working_hours").fetchone()[0],
            "countries": self.conn.execute("SELECT COUNT(DISTINCT country) FROM working_hours").fetchone()[0],
            "regions": self.conn.execute("SELECT COUNT(*) FROM region_summary").fetchone()[0],
            "years": self.query("SELECT MIN(year) as min_y, MAX(year) as max_y FROM working_hours").iloc[0].tolist(),
            "latest_avg_weekly": round(latest_avg, 1) if latest_avg else 0,
            "shortest_week_country": shortest['country'],
            "shortest_week_hours": round(shortest['latest_weekly_hours'], 1),
        }


if __name__ == "__main__":
    with WorkingHoursDatabase() as db:
        print("Stats:", db.get_stats())
