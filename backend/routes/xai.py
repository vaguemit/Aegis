"""
Advanced Explainable AI (XAI) Routes:
Multi-Head Attention Decomposition & Integrated Gradients Saliency.
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import torch

from backend.graph_manager import graph_manager
from src.analysis.advanced_xai import AdvancedXAIAnalyzer

router = APIRouter(prefix="/api/xai", tags=["Advanced XAI"])


class AdvancedXAIRequest(BaseModel):
    graph_id: str
    source_idx: int
    target_idx: int


@router.post("/decompose")
def decompose_edge_attention(req: AdvancedXAIRequest):
    """
    Decomposes GAT attention for edge (u -> v) across individual heads (Heads 1..4)
    and computes Integrated Gradients feature saliency.
    """
    graph_data = graph_manager.get_graph(req.graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    gat_model = graph_manager.models["gat"]
    analyzer = AdvancedXAIAnalyzer(gat_model)

    explanation = analyzer.explain_edge_comprehensively(
        u_idx=req.source_idx,
        v_idx=req.target_idx,
        x_matrix=graph_data.x_matrix,
        adj_tensor=graph_data.adj_tensor,
        node_names=graph_data.node_names,
    )

    return {
        "graph_id": req.graph_id,
        "source_idx": explanation.source_idx,
        "target_idx": explanation.target_idx,
        "source_name": explanation.source_name,
        "target_name": explanation.target_name,
        "predicted_probability": explanation.predicted_probability,
        "subgraph_importance": explanation.subgraph_importance_score,
        "tactical_rationale": explanation.tactical_rationale,
        "mitre_ttp": {
            "tactic": explanation.mitre_ttp.tactic_name,
            "technique_id": explanation.mitre_ttp.technique_id,
            "technique_name": explanation.mitre_ttp.technique_name,
            "description": explanation.mitre_ttp.description,
            "detection": explanation.mitre_ttp.detection_methods,
            "mitigations": explanation.mitre_ttp.mitigation_ids,
        },
        "head_attentions": [
            {
                "head": h.head_index,
                "semantic_role": h.head_semantic_role,
                "attention_weight": h.attention_weight,
                "interpretation": h.interpretation,
            }
            for h in explanation.head_attentions
        ],
        "integrated_gradients_saliency": explanation.integrated_gradient_saliency,
    }
