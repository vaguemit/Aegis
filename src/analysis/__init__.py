"""Explainable AI (XAI), MITRE ATT&CK Mapping, and Counterfactual Defense Analysis Module."""

from src.analysis.explainability import (
    GATExplainer,
    EdgeExplanation,
    PathExplanation,
)
from src.analysis.mitre_mapper import (
    MitreAttackMapper,
    MitreTechnique,
)
from src.analysis.advanced_xai import (
    AdvancedXAIAnalyzer,
    HeadAttentionDetail,
    AdvancedEdgeExplanation,
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
    "MitreAttackMapper",
    "MitreTechnique",
    "AdvancedXAIAnalyzer",
    "HeadAttentionDetail",
    "AdvancedEdgeExplanation",
    "CounterfactualDefenseEngine",
    "CounterfactualResult",
    "DefenseActionType",
]
