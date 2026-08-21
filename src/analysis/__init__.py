"""Explainable AI (XAI) and Counterfactual Defense Analysis Module."""

from src.analysis.explainability import (
    GATExplainer,
    EdgeExplanation,
    PathExplanation,
)
from src.analysis.counterfactual import (
    CounterfactualDefenseEngine,
    CounterfactualResult,
    DefenseActionType,
)

__all__ = [
    "GATExplainer",
    "EdgeExplanation",
    "PathExplanation",
    "CounterfactualDefenseEngine",
    "CounterfactualResult",
    "DefenseActionType",
]
