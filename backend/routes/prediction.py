"""
Attack Path Prediction Routes.
Handles GNN forward inference and constrained Top-K beam search.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException
import torch

from backend.models import (
    PredictRequest,
    PredictResponse,
    PredictedPathResponse,
    PathHopResponse,
)
from backend.graph_manager import graph_manager
from src.search.beam_search import ConstrainedBeamSearch
from src.search.feasibility import SecurityConstraintEngine

router = APIRouter(prefix="/api/predict", tags=["Prediction"])


@router.post("", response_model=PredictResponse)
def predict_attack_paths(req: PredictRequest):
    """
    Predicts the Top-K most probable attack paths from source to target asset.
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

    # Guarantee distinct starting foothold and target crown jewel
    if source_idx == target_idx and graph_data.num_nodes > 1:
        if graph_data.target_idx is not None and graph_data.target_idx != source_idx:
            target_idx = graph_data.target_idx
        elif source_idx == 0:
            target_idx = 1
        else:
            target_idx = 0

    model_key = req.model_type.lower()
    if model_key not in graph_manager.models:
        model_key = "gat"

    model = graph_manager.models[model_key]

    t0 = time.perf_counter()
    with torch.no_grad():
        if model_key == "dijkstra":
            edge_probs = model.predict_edge_probs(
                graph_data.adj_tensor, source_idx, target_idx
            )
        elif model_key == "cvss":
            edge_probs = model.predict_edge_probs(
                graph_data.adj_tensor, graph_data.x_matrix, source_idx, target_idx
            )
        else:
            edge_probs = model(graph_data.x_matrix, graph_data.adj_tensor)

    # Execute Constrained Beam Search
    constraint_engine = SecurityConstraintEngine()
    beam_searcher = ConstrainedBeamSearch(
        beam_width=req.beam_width,
        max_hops=req.max_hops,
        constraint_engine=constraint_engine,
    )

    ranked_paths = beam_searcher.search(
        edge_probs=edge_probs,
        adj_tensor=graph_data.adj_tensor,
        x_matrix=graph_data.x_matrix,
        source_idx=source_idx,
        target_idx=target_idx,
        node_names=graph_data.node_names,
        top_k=req.top_k,
    )
    t1 = time.perf_counter()
    exec_time_ms = (t1 - t0) * 1000.0

    # Format response
    path_responses: List[PredictedPathResponse] = []
    node_visitation = {}

    for p in ranked_paths:
        hop_responses: List[PathHopResponse] = [
            PathHopResponse(
                source_idx=h.source_idx,
                target_idx=h.target_idx,
                source_name=h.source_name,
                target_name=h.target_name,
                edge_type=h.edge_type,
                probability=h.probability,
                description=h.description,
            )
            for h in p.hops
        ]

        path_responses.append(
            PredictedPathResponse(
                rank=p.rank,
                nodes=p.nodes,
                node_names=p.node_names,
                confidence_score=p.confidence_score,
                cumulative_prob=p.cumulative_prob,
                hop_count=p.hop_count,
                hops=hop_responses,
            )
        )

        for n in p.nodes[1:-1]:
            node_visitation[n] = node_visitation.get(n, 0) + 1

    # Detect bottleneck pivot node
    bottleneck_idx = None
    bottleneck_name = None
    if node_visitation:
        bottleneck_idx = max(node_visitation, key=node_visitation.get)
        bottleneck_name = graph_data.node_names[bottleneck_idx] if graph_data.node_names else f"Node_{bottleneck_idx}"

    src_name = graph_data.node_names[source_idx] if graph_data.node_names else f"Node_{source_idx}"
    dst_name = graph_data.node_names[target_idx] if graph_data.node_names else f"Node_{target_idx}"

    return PredictResponse(
        graph_id=req.graph_id,
        model_used=model_key.upper(),
        source_idx=source_idx,
        target_idx=target_idx,
        source_name=src_name,
        target_name=dst_name,
        execution_time_ms=exec_time_ms,
        paths=path_responses,
        bottleneck_node_idx=bottleneck_idx,
        bottleneck_node_name=bottleneck_name,
    )
