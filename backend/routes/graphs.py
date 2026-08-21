"""
Graph management and generation routes.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models import (
    GraphSummary,
    GraphDetailResponse,
    SyntheticGenerateRequest,
)
from backend.graph_manager import graph_manager
from src.data.synthetic_generator import SyntheticEnterpriseGenerator

router = APIRouter(prefix="/api/graphs", tags=["Graphs"])


@router.get("", response_model=List[GraphSummary])
def list_graphs():
    """Returns a list of all loaded enterprise network graphs."""
    return graph_manager.list_graph_summaries()


@router.get("/{graph_id}", response_model=GraphDetailResponse)
def get_graph_details(graph_id: str):
    """Returns full Cytoscape-formatted graph details (nodes & multi-relational edges)."""
    detail = graph_manager.get_graph_detail(graph_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")
    return detail


@router.post("/generate", response_model=GraphDetailResponse)
def generate_synthetic_graph(req: SyntheticGenerateRequest):
    """Synthesizes a new enterprise network topology with Active Directory features."""
    generator = SyntheticEnterpriseGenerator(
        num_computers=req.num_computers,
        num_servers=req.num_servers,
        num_users=req.num_users,
        num_ous=req.num_ous,
        num_gpos=req.num_gpos,
        num_domain_controllers=req.num_domain_controllers,
        cve_probability=req.cve_probability,
        spn_probability=req.spn_probability,
        seed=req.seed,
    )
    scenario_title = req.scenario_name or f"syn_enterprise_{req.num_computers + req.num_servers + req.num_users}n"
    graph_data = generator.generate(scenario_name=scenario_title)

    graph_manager.add_synthetic_graph(graph_data)
    detail = graph_manager.get_graph_detail(graph_data.graph_id)
    return detail
