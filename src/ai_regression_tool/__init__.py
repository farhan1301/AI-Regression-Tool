"""AI Regression Tool.

A small, dependency-light utility to compare two metric JSON files
and fail CI if important metrics regress beyond a threshold.
"""

__all__ = ["compare_metrics", "load_metrics"]

from .core import compare_metrics, load_metrics
