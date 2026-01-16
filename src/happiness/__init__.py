"""World Happiness Report analysis module."""

from .pipeline import run_happiness_pipeline
from .database import HappinessDatabase

__all__ = ["run_happiness_pipeline", "HappinessDatabase"]
