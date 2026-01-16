"""CO2 Emissions by Sector analysis module."""

from .pipeline import run_co2_emissions_pipeline
from .database import CO2EmissionsDatabase

__all__ = ["run_co2_emissions_pipeline", "CO2EmissionsDatabase"]
