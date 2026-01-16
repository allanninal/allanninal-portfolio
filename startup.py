"""
Startup script for AWS App Runner.
Generates databases from CSV files, then starts Streamlit.
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def run_pipelines():
    """Run all data pipelines to generate DuckDB databases."""
    logger.info("Starting database generation...")

    pipelines = [
        "src.pipeline",  # Main media perception pipeline
        "src.happiness.pipeline",
        "src.mobile_data.pipeline",
        "src.maddison.database",
        "src.life_expectancy.database",
        "src.plastic_waste.database",
        "src.natural_disasters.database",
        "src.technology_adoption.pipeline",
        "src.food_affordability.pipeline",
        "src.time_with_people.pipeline",
        "src.female_labor.pipeline",
        "src.gender_wage_gap.pipeline",
        "src.working_hours.pipeline",
        "src.learning_adjusted.pipeline",
        "src.education_quality.pipeline",
        "src.tree_density.pipeline",
        "src.air_pollution.pipeline",
        "src.co2_emissions.pipeline",
        "src.plastic_ocean.pipeline",
        "src.suicide_rates.pipeline",
        "src.energy_deaths.pipeline",
        "src.mental_health.pipeline",
        "src.healthcare_quality.pipeline",
        "src.child_mortality.pipeline",
        "src.poverty_lines.pipeline",
        "src.gini_coefficients.pipeline",
        "src.poverty_inequality.pipeline",
        "src.loneliness_older_adults.pipeline",
    ]

    for pipeline in pipelines:
        try:
            logger.info(f"Running {pipeline}...")
            module = __import__(pipeline, fromlist=[''])
            if hasattr(module, 'run_pipeline'):
                module.run_pipeline()
            elif hasattr(module, '__name__'):
                # For database modules that run on import
                pass
            logger.info(f"Completed {pipeline}")
        except Exception as e:
            logger.warning(f"Pipeline {pipeline} failed: {e}")

    logger.info("Database generation complete!")


def start_streamlit():
    """Start Streamlit server."""
    logger.info("Starting Streamlit...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "Home.py",
        "--server.port=8080",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ])


if __name__ == "__main__":
    run_pipelines()
    start_streamlit()
