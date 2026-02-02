"""AI Regression Tool.

A small, dependency-light utility to compare two metric JSON files
and fail CI if important metrics regress beyond a threshold.
"""

__all__ = ["__version__", "compare_metrics", "load_metrics"]

# Keep this in sync with pyproject.toml
__version__ = "0.1.1"

from .core import compare_metrics, load_metrics
