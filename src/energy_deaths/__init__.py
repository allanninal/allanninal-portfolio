"""Deaths per TWh Energy Production analysis module."""

from .pipeline import run_energy_deaths_pipeline
from .database import EnergyDeathsDatabase

__all__ = ["run_energy_deaths_pipeline", "EnergyDeathsDatabase"]
