"""Suicide Rates by Sex and Age analysis module."""

from .pipeline import run_suicide_rates_pipeline
from .database import SuicideRatesDatabase

__all__ = ["run_suicide_rates_pipeline", "SuicideRatesDatabase"]
