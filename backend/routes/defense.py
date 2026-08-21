"""
Counterfactual Defense Simulation & Mitigation Recommendation Routes.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
import torch

from backend.models import (
    DefenseSimulateRequest,
    DefenseSimulateResponse,
    RecommendDefenseRequest,
    PredictedPathResponse,
    PathHopResponse,
)
from backend.graph_manager import graph_manager
from src.analysis.counterfactual import CounterfactualDefenseEngine, DefenseActionType
from src.search.beam_search import ConstrainedBeamSearch
from src.data.schema import EdgeType

router = APIRouter(prefix="/api/defense", tags=["Counterfactual Defense"])


def _format_predicted_path(path_obj) -> Optional[PredictedPathResponse]:
    """Helper to convert PredictedAttackPath to Pydantic model."""
    if path_obj is None:
        return None
    hops = [
        PathHopResponse(
            source_idx=h.source_idx,
            target_idx=h.target_idx,
            source_name=h.source_name,
            target_name=h.target_name,
            edge_type=h.edge_type,
            probability=h.probability,
            description=h.description,
        )
        for h in path_obj.hops
    ]
    return PredictedPathResponse(
        rank=path_obj.rank,
        nodes=path_obj.nodes,
        node_names=path_obj.node_names,
        confidence_score=path_obj.confidence_score,
        cumulative_prob=path_obj.cumulative_prob,
        hop_count=path_obj.hop_count,
        hops=hops,
    )


@router.post("/simulate", response_model=DefenseSimulateResponse)
def simulate_defense_action(req: DefenseSimulateRequest):
    """
    Simulates applying a patch or disabling a service on a cloned graph state,
    calculating the resulting risk reduction and path diversion.
    """
    graph_data = graph_manager.get_graph(req.graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    source_idx = req.source_idx if req.source_idx is not None else graph_data.source_idx
    target_idx = req.target_idx if req.target_idx is not None else graph_data.target_idx

    if source_idx is None:
        source_idx = 0
    if target_idx is None:
        target_idx = graph_data.num_nodes - 1

    gat_model = graph_manager.models["gat"]
    defense_engine = CounterfactualDefenseEngine(gat_model)

    if req.action_type == "patch":
        if req.target_node_idx is None:
            raise HTTPException(status_code=400, detail="target_node_idx required for patch action")

        result = defense_engine.simulate_patch_vulnerability(
            x_matrix=graph_data.x_matrix,
            adj_tensor=graph_data.adj_tensor,
            node_idx=req.target_node_idx,
            source_idx=source_idx,
            target_idx=target_idx,
            node_names=graph_data.node_names,
        )
    elif req.action_type == "disable_service":
        if req.edge_u is None or req.edge_v is None or req.edge_type is None:
            raise HTTPException(status_code=400, detail="edge_u, edge_v, and edge_type required for disable_service action")

        try:
            edge_type_enum = EdgeType(req.edge_type)
        except ValueError:
            edge_type_enum = EdgeType.OPEN

        result = defense_engine.simulate_disable_service(
            x_matrix=graph_data.x_matrix,
            adj_tensor=graph_data.adj_tensor,
            source_idx=source_idx,
            target_idx=target_idx,
            edge_u=req.edge_u,
            edge_v=req.edge_v,
            edge_type=edge_type_enum,
            node_names=graph_data.node_names,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action_type: {req.action_type}")

    return DefenseSimulateResponse(
        action_type=result.action_type.value,
        action_description=result.action_description,
        original_risk_score=result.original_risk_score,
        mitigated_risk_score=result.mitigated_risk_score,
        delta_risk=result.delta_risk,
        risk_reduction_pct=result.risk_reduction_pct,
        path_was_diverted=result.path_was_diverted,
        path_was_severed=result.path_was_severed,
        recommendation_verdict=result.recommendation_verdict,
        original_path=_format_predicted_path(result.original_path),
        mitigated_path=_format_predicted_path(result.mitigated_path),
    )


@router.post("/recommend", response_model=List[DefenseSimulateResponse])
def recommend_optimal_defenses(req: RecommendDefenseRequest):
    """
    Automated Decision Support: Identifies the top-N most effective defensive mitigations
    along the predicted attack path to maximize risk reduction.
    """
    graph_data = graph_manager.get_graph(req.graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    source_idx = req.source_idx if req.source_idx is not None else graph_data.source_idx
    target_idx = req.target_idx if req.target_idx is not None else graph_data.target_idx

    if source_idx is None:
        source_idx = 0
    if target_idx is None:
        target_idx = graph_data.num_nodes - 1

    gat_model = graph_manager.models["gat"]
    beam_searcher = ConstrainedBeamSearch(beam_width=3, max_hops=12)
    defense_engine = CounterfactualDefenseEngine(gat_model, beam_searcher=beam_searcher)

    # 1. Obtain baseline path
    with torch.no_grad():
        edge_probs = gat_model(graph_data.x_matrix, graph_data.adj_tensor)

    paths = beam_searcher.search(
        edge_probs=edge_probs,
        adj_tensor=graph_data.adj_tensor,
        x_matrix=graph_data.x_matrix,
        source_idx=source_idx,
        target_idx=target_idx,
        node_names=graph_data.node_names,
        top_k=1,
    )
    if not paths:
        return []

    recommendations = defense_engine.recommend_optimal_defenses(
        x_matrix=graph_data.x_matrix,
        adj_tensor=graph_data.adj_tensor,
        predicted_path=paths[0],
        source_idx=source_idx,
        target_idx=target_idx,
        node_names=graph_data.node_names,
        top_n=req.top_n,
    )

    return [
        DefenseSimulateResponse(
            action_type=r.action_type.value,
            action_description=r.action_description,
            original_risk_score=r.original_risk_score,
            mitigated_risk_score=r.mitigated_risk_score,
            delta_risk=r.delta_risk,
            risk_reduction_pct=r.risk_reduction_pct,
            path_was_diverted=r.path_was_diverted,
            path_was_severed=r.path_was_severed,
            recommendation_verdict=r.recommendation_verdict,
            original_path=_format_predicted_path(r.original_path),
            mitigated_path=_format_predicted_path(r.mitigated_path),
        )
        for r in recommendations
    ]
