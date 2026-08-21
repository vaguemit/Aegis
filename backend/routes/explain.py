"""
Explainability & Attention Attribution Routes.
"""

from typing import List
from fastapi import APIRouter, HTTPException

from backend.models import (
    ExplainRequest,
    ExplainResponse,
    EdgeExplanationResponse,
)
from backend.graph_manager import graph_manager
from src.analysis.explainability import GATExplainer

router = APIRouter(prefix="/api/explain", tags=["Explainability"])


@router.post("", response_model=ExplainResponse)
def explain_attack_path(req: ExplainRequest):
    """
    Computes GAT attention weights and feature contributions for a specified attack trajectory.
    """
    graph_data = graph_manager.get_graph(req.graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    if not req.path_nodes or len(req.path_nodes) < 2:
        raise HTTPException(status_code=400, detail="Path must contain at least 2 nodes")

    gat_model = graph_manager.models["gat"]
    explainer = GATExplainer(gat_model)

    path_exp = explainer.explain_path(
        path_nodes=req.path_nodes,
        x_matrix=graph_data.x_matrix,
        adj_tensor=graph_data.adj_tensor,
        node_names=graph_data.node_names,
    )

    edge_exp_responses = [
        EdgeExplanationResponse(
            source_idx=e.source_idx,
            target_idx=e.target_idx,
            source_name=e.source_name,
            target_name=e.target_name,
            predicted_probability=e.predicted_probability,
            gat_attention_score=e.gat_attention_score,
            dominant_relation=e.dominant_relation,
            top_contributing_features=[[feat, score] for feat, score in e.top_contributing_features],
            summary=e.summary,
        )
        for e in path_exp.edge_explanations
    ]

    return ExplainResponse(
        graph_id=req.graph_id,
        overall_confidence=path_exp.overall_confidence,
        bottleneck_node_idx=path_exp.bottleneck_node_idx,
        bottleneck_node_name=path_exp.bottleneck_node_name,
        edge_explanations=edge_exp_responses,
        key_findings=path_exp.key_findings,
    )
