"""Air Pollution Deaths analysis module."""

from .pipeline import run_air_pollution_pipeline
from .database import AirPollutionDatabase

__all__ = ["run_air_pollution_pipeline", "AirPollutionDatabase"]
