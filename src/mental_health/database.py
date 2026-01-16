"""
DuckDB database for Mental Health Services data (Wang et al. 2007).
"""

import pandas as pd
from pathlib import Path
from loguru import logger

from src.shared.base_database import BaseDatabase


class MentalHealthDatabase(BaseDatabase):
    """Database manager for mental health services data."""

    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "mental_health.duckdb"
    PROJECT_NAME = "Mental Health Services"

    def create_schema(self):
        """Create database schema."""
        logger.info("Creating mental health database schema...")

        # Main data table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS mental_health (
                country VARCHAR,
                year INTEGER,
                gdp_healthcare DOUBLE,
                any_treatment DOUBLE,
                specialty_pct DOUBLE,
                general_medical_pct DOUBLE,
                human_services_pct DOUBLE,
                alternative_pct DOUBLE,
                severe_treated DOUBLE,
                moderate_treated DOUBLE,
                mild_treated DOUBLE,
                income_group VARCHAR,
                treatment_gap VARCHAR,
                severe_untreated DOUBLE,
                moderate_untreated DOUBLE,
                mild_untreated DOUBLE,
                primary_service VARCHAR
            )
        """)

        # Income group summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS income_summary (
                income_group VARCHAR,
                countries INTEGER,
                avg_gdp_health DOUBLE,
                avg_any_treatment DOUBLE,
                avg_severe_treated DOUBLE,
                avg_moderate_treated DOUBLE,
                avg_mild_treated DOUBLE
            )
        """)

        # Service type summary
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS service_summary (
                service_type VARCHAR,
                avg_usage DOUBLE,
                min_usage DOUBLE,
                max_usage DOUBLE
            )
        """)

        logger.info("Schema created successfully")

    def load_data(self, main_df: pd.DataFrame, income_df: pd.DataFrame,
                  service_df: pd.DataFrame):
        """Load all dataframes into database."""
        logger.info("Loading data into database...")

        tables = ["mental_health", "income_summary", "service_summary"]
        for table in tables:
            self.conn.execute(f"DELETE FROM {table}")

        self.conn.execute("INSERT INTO mental_health SELECT * FROM main_df")
        logger.info(f"Loaded {len(main_df)} rows into mental_health")

        self.conn.execute("INSERT INTO income_summary SELECT * FROM income_df")
        logger.info(f"Loaded {len(income_df)} rows into income_summary")

        self.conn.execute("INSERT INTO service_summary SELECT * FROM service_df")
        logger.info(f"Loaded {len(service_df)} rows into service_summary")

    def get_full_data(self) -> pd.DataFrame:
        """Get all mental health data."""
        return self.query("SELECT * FROM mental_health ORDER BY any_treatment DESC")

    def get_income_summary(self) -> pd.DataFrame:
        """Get income group summary."""
        return self.query("""
            SELECT * FROM income_summary
            ORDER BY CASE income_group
                WHEN 'High Income' THEN 1
                WHEN 'Upper-Middle' THEN 2
                WHEN 'Lower-Middle' THEN 3
                WHEN 'Low Income' THEN 4
                ELSE 5
            END
        """)

    def get_service_summary(self) -> pd.DataFrame:
        """Get service type summary."""
        return self.query("SELECT * FROM service_summary ORDER BY avg_usage DESC")

    def get_by_treatment_rate(self) -> pd.DataFrame:
        """Get countries sorted by any treatment rate."""
        return self.query("""
            SELECT country, income_group, any_treatment, severe_treated,
                   moderate_treated, mild_treated, treatment_gap
            FROM mental_health
            ORDER BY any_treatment DESC
        """)

    def get_by_severe_treatment(self) -> pd.DataFrame:
        """Get countries sorted by severe mental illness treatment rate."""
        return self.query("""
            SELECT country, income_group, severe_treated, severe_untreated,
                   treatment_gap
            FROM mental_health
            ORDER BY severe_treated DESC
        """)

    def get_by_income_group(self, income_group: str) -> pd.DataFrame:
        """Get countries by income group."""
        return self.query(f"""
            SELECT * FROM mental_health
            WHERE income_group = '{income_group}'
            ORDER BY any_treatment DESC
        """)

    def get_service_breakdown(self, country: str) -> pd.DataFrame:
        """Get service type breakdown for a country."""
        data = self.query(f"""
            SELECT specialty_pct, general_medical_pct, human_services_pct, alternative_pct
            FROM mental_health
            WHERE country = '{country}'
        """)
        if len(data) == 0:
            return pd.DataFrame()

        return pd.DataFrame({
            "service_type": ["Mental Health Specialty", "General Medical", "Human Services", "Alternative Medicine"],
            "percentage": [
                data.iloc[0]["specialty_pct"],
                data.iloc[0]["general_medical_pct"],
                data.iloc[0]["human_services_pct"],
                data.iloc[0]["alternative_pct"]
            ]
        })

    def get_severity_breakdown(self, country: str) -> pd.DataFrame:
        """Get severity-based treatment for a country."""
        data = self.query(f"""
            SELECT severe_treated, moderate_treated, mild_treated
            FROM mental_health
            WHERE country = '{country}'
        """)
        if len(data) == 0:
            return pd.DataFrame()

        return pd.DataFrame({
            "severity": ["Severe", "Moderate", "Mild"],
            "treated_pct": [
                data.iloc[0]["severe_treated"],
                data.iloc[0]["moderate_treated"],
                data.iloc[0]["mild_treated"]
            ],
            "untreated_pct": [
                100 - data.iloc[0]["severe_treated"],
                100 - data.iloc[0]["moderate_treated"],
                100 - data.iloc[0]["mild_treated"]
            ]
        })

    def get_treatment_gaps(self) -> pd.DataFrame:
        """Get treatment gaps by severity."""
        return self.query("""
            SELECT country, income_group,
                   severe_untreated, moderate_untreated, mild_untreated
            FROM mental_health
            ORDER BY severe_untreated DESC
        """)

    def get_country_data(self, country: str) -> pd.DataFrame:
        """Get data for a specific country."""
        return self.query(f"""
            SELECT * FROM mental_health
            WHERE country = '{country}'
        """)

    def get_countries_list(self):
        """Get list of all countries."""
        result = self.query("SELECT DISTINCT country FROM mental_health ORDER BY country")
        return result['country'].tolist()

    def get_stats(self) -> dict:
        """Get database statistics."""
        data = self.get_full_data()

        highest = data.iloc[0]
        lowest = data.iloc[-1]

        return {
            "project": self.PROJECT_NAME,
            "countries": len(data),
            "income_groups": self.conn.execute("SELECT COUNT(DISTINCT income_group) FROM mental_health").fetchone()[0],
            "highest_treatment_country": highest['country'],
            "highest_treatment": highest['any_treatment'],
            "lowest_treatment_country": lowest['country'],
            "lowest_treatment": lowest['any_treatment'],
            "avg_any_treatment": data['any_treatment'].mean(),
            "avg_severe_treated": data['severe_treated'].mean(),
            "avg_moderate_treated": data['moderate_treated'].mean(),
            "avg_mild_treated": data['mild_treated'].mean(),
            "avg_gdp_health": data['gdp_healthcare'].mean(),
            "treatment_range": highest['any_treatment'] - lowest['any_treatment'],
        }


if __name__ == "__main__":
    with MentalHealthDatabase() as db:
        print("Stats:", db.get_stats())
