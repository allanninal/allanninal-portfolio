"""Plastic Ocean Pollution analysis module."""

from .pipeline import run_plastic_ocean_pipeline
from .database import PlasticOceanDatabase

__all__ = ["run_plastic_ocean_pipeline", "PlasticOceanDatabase"]
