"""
Outsider Node and Insider Bridge API Router.
Provides endpoints for injecting outsider threats, detecting anomalous bridges,
evaluating risk elevation deltas, and executing counterfactual severance defenses.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.data.schema import EdgeType
from src.defense.outsider_schema import (
    OutsiderType,
    BridgeMechanism,
    BridgeRemediationAction,
)
from src.defense.outsider_engine import OutsiderThreatEngine
from src.defense.bridge_detector import AnomalousBridgeDetector
from src.defense.risk_elevation import OutsiderRiskEvaluator
from src.defense.outsider_counterfactual import OutsiderCounterfactualEngine
from src.defense.outsider_remediation import OutsiderRemediationPlanner
from backend.graph_manager import graph_manager

router = APIRouter(prefix="/api/outsiders", tags=["outsiders"])

outsider_engine = OutsiderThreatEngine(seed=42)
bridge_detector = AnomalousBridgeDetector(anomaly_threshold=0.6)
risk_evaluator = OutsiderRiskEvaluator()
counterfactual_engine = OutsiderCounterfactualEngine()
remediation_planner = OutsiderRemediationPlanner()


class InjectOutsiderRequest(BaseModel):
    insider_node_idx: Optional[int] = None
    threat_vector: Optional[str] = "REVERSE_TUNNEL"   # REVERSE_TUNNEL | DUAL_HOMED_NIC | SHADOW_VM
    outsider_name: Optional[str] = None


class SeverBridgeRequest(BaseModel):
    insider_node_idx: int
    outsider_node_idx: int


class IsolateInsiderRequest(BaseModel):
    insider_node_idx: int


@router.post("/inject")
def inject_outsider(req: InjectOutsiderRequest) -> Dict[str, Any]:
    """Injects an outsider node bridged through an internal domain node into current graph."""
    current_g = graph_manager.get_graph()
    if current_g is None:
        raise HTTPException(status_code=400, detail="No active graph loaded in graph_manager.")

    insider_idx = req.insider_node_idx
    if insider_idx is None:
        # Pick workstation or server
        for i in range(current_g.num_nodes):
            name = current_g.node_names[i].lower() if current_g.node_names else ""
            if "dc" not in name and i != current_g.target_idx:
                insider_idx = i
                break
        if insider_idx is None:
            insider_idx = 0

    vector = (req.threat_vector or "REVERSE_TUNNEL").upper()
    if vector == "DUAL_HOMED_NIC":
        new_g, o_meta, b_meta = outsider_engine.inject_dual_homed_nic(current_g, insider_idx)
    elif vector == "SHADOW_VM":
        new_g, o_meta, b_meta = outsider_engine.inject_shadow_vm(current_g, insider_idx)
    else:
        new_g, o_meta, b_meta = outsider_engine.inject_covert_tunnel(current_g, insider_idx)

    # Update active graph in memory
    graph_manager.set_graph(new_g)

    # Compute risk elevation
    risk_info = risk_evaluator.evaluate_risk_elevation(
        baseline_graph=current_g,
        injected_graph=new_g,
        outsider_idx=new_g.num_nodes - 1,
        insider_idx=insider_idx,
    )

    return {
        "success": True,
        "outsider_node": {
            "node_id": o_meta.node_id,
            "name": o_meta.name,
            "type": o_meta.outsider_type.value,
            "ip": o_meta.ip_address,
            "mac": o_meta.mac_address,
            "introduced_by": o_meta.introduced_by_node_name,
        },
        "bridge": {
            "bridge_id": b_meta.bridge_id,
            "mechanism": b_meta.mechanism.value,
            "protocol": b_meta.protocol,
            "port": b_meta.port,
            "mitre": b_meta.mitre_techniques,
        },
        "risk_elevation": risk_info,
        "new_graph_nodes": new_g.num_nodes,
    }


@router.get("/detect")
def detect_bridges() -> List[Dict[str, Any]]:
    """Runs anomalous bridge detection on currently active graph."""
    current_g = graph_manager.get_graph()
    if current_g is None:
        raise HTTPException(status_code=400, detail="No active graph loaded.")
    return bridge_detector.detect_bridges(current_g)


@router.post("/sever")
def sever_bridge(req: SeverBridgeRequest) -> Dict[str, Any]:
    """Counterfactually severs the edge connecting insider and outsider nodes."""
    current_g = graph_manager.get_graph()
    if current_g is None:
        raise HTTPException(status_code=400, detail="No active graph loaded.")

    severed_g, metrics = counterfactual_engine.sever_bridge(
        graph_data=current_g,
        insider_idx=req.insider_node_idx,
        outsider_idx=req.outsider_node_idx,
    )
    graph_manager.set_graph(severed_g)

    return {
        "success": True,
        "metrics": metrics,
        "num_nodes": severed_g.num_nodes,
        "message": f"Bridge severed between node {req.insider_node_idx} and outsider {req.outsider_node_idx}.",
    }


@router.post("/isolate-insider")
def isolate_insider(req: IsolateInsiderRequest) -> Dict[str, Any]:
    """Isolates the insider host completely from the network."""
    current_g = graph_manager.get_graph()
    if current_g is None:
        raise HTTPException(status_code=400, detail="No active graph loaded.")

    isolated_g, metrics = counterfactual_engine.isolate_insider_host(
        graph_data=current_g,
        insider_idx=req.insider_node_idx,
    )
    graph_manager.set_graph(isolated_g)

    return {
        "success": True,
        "metrics": metrics,
        "message": f"Insider node {req.insider_node_idx} isolated from domain.",
    }


@router.get("/remediation-plan")
def get_remediation_plan(insider_idx: int = Query(0), outsider_idx: int = Query(1)) -> Dict[str, Any]:
    """Generates a complete SOC remediation plan with MITRE ATT&CK mitigations."""
    current_g = graph_manager.get_graph()
    ins_name = current_g.node_names[insider_idx] if current_g and current_g.node_names else f"node_{insider_idx}"
    out_name = current_g.node_names[outsider_idx] if current_g and current_g.node_names else f"node_{outsider_idx}"

    from src.defense.outsider_schema import InsiderBridge, BridgeMechanism
    bridge = InsiderBridge(
        bridge_id=f"bridge-{insider_idx}-{outsider_idx}",
        insider_node_idx=insider_idx,
        outsider_node_idx=outsider_idx,
        insider_name=ins_name,
        outsider_name=out_name,
        mechanism=BridgeMechanism.SOCKS_CHISEL_TUNNEL,
    )
    plan = remediation_planner.build_plan(bridge=bridge, baseline_risk=0.91)

    return {
        "plan_id": plan.plan_id,
        "bridge_id": plan.bridge_id,
        "insider_name": plan.insider_name,
        "outsider_name": plan.outsider_name,
        "actions": [a.value for a in plan.actions],
        "baseline_risk": plan.baseline_risk,
        "remediated_risk": plan.remediated_risk,
        "delta_risk_percent": plan.delta_risk_percent,
        "mitre_mitigations": plan.mitre_mitigations,
        "audit_log": plan.audit_log,
    }
