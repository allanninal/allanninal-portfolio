"""Poverty and Inequality Platform analysis module."""

from .pipeline import run_poverty_inequality_pipeline
from .database import PovertyInequalityDatabase

__all__ = ["run_poverty_inequality_pipeline", "PovertyInequalityDatabase"]
