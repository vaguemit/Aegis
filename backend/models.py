"""
Pydantic API Schemas for AegisPath FastAPI Backend.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class GraphSummary(BaseModel):
    graph_id: str
    num_nodes: int
    num_edges: int
    num_vulnerable_nodes: int
    num_high_value_nodes: int
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None
    source_name: Optional[str] = None
    target_name: Optional[str] = None


class NodeElement(BaseModel):
    id: str
    index: int
    name: str
    entity_type: str
    os: Optional[str] = None
    is_enabled: bool = True
    has_spn: bool = False
    is_high_value: bool = False
    is_vulnerable: bool = False
    is_target: bool = False
    is_owned: bool = False


class EdgeElement(BaseModel):
    id: str
    source: str
    target: str
    source_idx: int
    target_idx: int
    edge_type: str
    is_attack_path: bool = False


class GraphDetailResponse(BaseModel):
    graph_id: str
    num_nodes: int
    num_edges: int
    source_idx: Optional[int]
    target_idx: Optional[int]
    nodes: List[NodeElement]
    edges: List[EdgeElement]


class SyntheticGenerateRequest(BaseModel):
    scenario_name: Optional[str] = None
    num_computers: int = 35
    num_servers: int = 8
    num_users: int = 60
    num_ous: int = 4
    num_gpos: int = 3
    num_domain_controllers: int = 1
    cve_probability: float = 0.25
    spn_probability: float = 0.15
    seed: Optional[int] = None


class PathHopResponse(BaseModel):
    source_idx: int
    target_idx: int
    source_name: str
    target_name: str
    edge_type: str
    probability: float
    description: str


class PredictedPathResponse(BaseModel):
    rank: int
    nodes: List[int]
    node_names: List[str]
    confidence_score: float
    cumulative_prob: float
    hop_count: int
    hops: List[PathHopResponse]


class PredictRequest(BaseModel):
    graph_id: str
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None
    model_type: str = "gat" # "gat", "gcn", "graphsage", "dijkstra", "cvss"
    top_k: int = 3
    beam_width: int = 5
    max_hops: int = 12


class PredictResponse(BaseModel):
    graph_id: str
    model_used: str
    source_idx: int
    target_idx: int
    source_name: str
    target_name: str
    execution_time_ms: float
    paths: List[PredictedPathResponse]
    bottleneck_node_idx: Optional[int] = None
    bottleneck_node_name: Optional[str] = None


class ExplainRequest(BaseModel):
    graph_id: str
    path_nodes: List[int]


class EdgeExplanationResponse(BaseModel):
    source_idx: int
    target_idx: int
    source_name: str
    target_name: str
    predicted_probability: float
    gat_attention_score: float
    dominant_relation: str
    top_contributing_features: List[List[Union[str, float]]]
    summary: str


class ExplainResponse(BaseModel):
    graph_id: str
    overall_confidence: float
    bottleneck_node_idx: int
    bottleneck_node_name: str
    edge_explanations: List[EdgeExplanationResponse]
    key_findings: List[str]


class DefenseSimulateRequest(BaseModel):
    graph_id: str
    action_type: str = "patch" # "patch" or "disable_service"
    target_node_idx: Optional[int] = None
    edge_u: Optional[int] = None
    edge_v: Optional[int] = None
    edge_type: Optional[str] = None
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None


class DefenseSimulateResponse(BaseModel):
    action_type: str
    action_description: str
    original_risk_score: float
    mitigated_risk_score: float
    delta_risk: float
    risk_reduction_pct: float
    path_was_diverted: bool
    path_was_severed: bool
    recommendation_verdict: str
    original_path: PredictedPathResponse
    mitigated_path: Optional[PredictedPathResponse] = None


class RecommendDefenseRequest(BaseModel):
    graph_id: str
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None
    top_n: int = 3
