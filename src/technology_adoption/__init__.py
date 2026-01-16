"""Technology Adoption analysis module."""

from .pipeline import run_technology_adoption_pipeline
from .database import TechnologyAdoptionDatabase

__all__ = ["run_technology_adoption_pipeline", "TechnologyAdoptionDatabase"]
