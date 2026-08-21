"""
Virtual Machine Simulation & Live Telemetry Playback Routes.
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import torch

from backend.graph_manager import graph_manager
from src.simulation.vm_engine import EnterpriseVMSimulator
from src.simulation.attack_player import LiveAttackPlaybackEngine
from src.search.beam_search import ConstrainedBeamSearch

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

# Global simulator instances
vm_sim = EnterpriseVMSimulator(seed=42)
playback_engine = LiveAttackPlaybackEngine(vm_sim)


class PlaybackRequest(BaseModel):
    graph_id: str
    path_nodes: Optional[List[int]] = None
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None


@router.get("/vms/{graph_id}")
def get_simulated_vms(graph_id: str):
    """Returns virtual machine hardware instances and hypervisor allocations."""
    graph_data = graph_manager.get_graph(graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")

    vms = vm_sim.build_vms_from_graph(graph_data)
    return {
        "graph_id": graph_id,
        "total_vms": len(vms),
        "hypervisor_hosts": [
            {
                "host_id": h.host_id,
                "host_name": h.host_name,
                "type": h.hypervisor_type.value,
                "cpu_cores": h.total_cpu_cores,
                "ram_gb": h.total_ram_gb,
                "vm_count": len(h.hosted_vm_ids),
            }
            for h in vm_sim.hypervisors.values()
        ],
        "virtual_machines": [
            {
                "vm_id": v.vm_id,
                "vm_name": v.vm_name,
                "node_index": v.node_index,
                "hostname": v.hostname,
                "os": v.os_name,
                "ip": v.network_adapters[0].ip_address,
                "subnet": v.network_adapters[0].subnet,
                "vlan": v.network_adapters[0].vlan_id,
                "state": v.state.value,
                "cpu_cores": v.cpu_cores,
                "ram_gb": v.ram_gb,
                "open_ports": v.open_ports,
                "services": v.running_services,
                "cves": v.active_cves,
                "privilege": v.privilege_level,
                "is_crown_jewel": v.is_crown_jewel,
            }
            for v in vms
        ],
    }


@router.post("/play")
def play_live_attack(req: PlaybackRequest):
    """
    Generates synchronized real-time attack step timeline with syslog and MITRE ATT&CK TTPs.
    """
    graph_data = graph_manager.get_graph(req.graph_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail=f"Graph '{req.graph_id}' not found")

    vm_sim.build_vms_from_graph(graph_data)

    gat_model = graph_manager.models["gat"]
    with torch.no_grad():
        edge_probs = gat_model(graph_data.x_matrix, graph_data.adj_tensor)

    path_nodes = req.path_nodes
    if not path_nodes:
        # Compute top path
        src = req.source_idx if req.source_idx is not None else (graph_data.source_idx or 0)
        dst = req.target_idx if req.target_idx is not None else (graph_data.target_idx or graph_data.num_nodes - 1)
        bs = ConstrainedBeamSearch(beam_width=1)
        paths = bs.search(
            edge_probs=edge_probs,
            adj_tensor=graph_data.adj_tensor,
            x_matrix=graph_data.x_matrix,
            source_idx=src,
            target_idx=dst,
            node_names=graph_data.node_names,
            top_k=1,
        )
        path_nodes = paths[0].nodes if paths else [src, dst]

    events = playback_engine.prepare_attack_timeline(
        path_nodes=path_nodes,
        node_names=graph_data.node_names or [f"Node_{i}" for i in range(graph_data.num_nodes)],
        adj_tensor=graph_data.adj_tensor,
        edge_probs=edge_probs,
    )

    return {
        "graph_id": req.graph_id,
        "path_nodes": path_nodes,
        "total_steps": len(events),
        "timeline": [
            {
                "step": e.step_number,
                "timestamp": e.timestamp,
                "source_vm": e.source_vm_name,
                "source_ip": e.source_ip,
                "target_vm": e.target_vm_name,
                "target_ip": e.target_ip,
                "edge_type": e.edge_type,
                "mitre_tactic": e.mitre_tactic,
                "mitre_technique": f"{e.mitre_technique_id} - {e.mitre_technique_name}",
                "probability": e.transition_probability,
                "syslog": e.syslog_entry,
                "compromised_nodes": e.compromised_node_indices,
                "status": e.status_summary,
            }
            for e in events
        ],
    }
