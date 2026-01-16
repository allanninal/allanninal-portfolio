"""Child Mortality Rates analysis module."""

from .pipeline import run_child_mortality_pipeline
from .database import ChildMortalityDatabase

__all__ = ["run_child_mortality_pipeline", "ChildMortalityDatabase"]
