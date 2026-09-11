"""
Anomalous Insider-Outsider Bridge Detector.
Leverages Graph Attention Network (GAT) multi-head attention weights,
relational adjacency bottlenecks, and zero-trust domain boundaries to detect
unauthorized bridges introduced by internal assets.
"""

from typing import Dict, List, Optional, Tuple, Any
import torch
import numpy as np

from src.data.schema import NetworkGraphData, NUM_EDGE_TYPES
from src.defense.outsider_schema import InsiderBridge, BridgeMechanism


class AnomalousBridgeDetector:
    """
    Detects unauthorized or anomalous boundary bridges connecting internal enterprise nodes
    to outsider entities using attention bottlenecks and structural graph heuristics.
    """

    def __init__(self, anomaly_threshold: float = 0.65):
        self.anomaly_threshold = anomaly_threshold

    def detect_bridges(
        self,
        graph_data: NetworkGraphData,
        attention_weights: Optional[torch.Tensor] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scans graph topology and attention matrices to pinpoint insider-outsider bridges.
        Returns list of detected bridge records with confidence scores and attribution.
        """
        detected = []
        outsider_indices = set(graph_data.get_outsider_indices())

        # If no explicit outsider tag, look for boundary crossing heuristics (e.g. leaf nodes with high-risk ports or names)
        num_nodes = graph_data.num_nodes
        adj = graph_data.adj_tensor.cpu().numpy()

        for u in range(num_nodes):
            for v in range(num_nodes):
                if u == v:
                    continue

                total_edge_weight = float(adj[u, v].sum())
                if total_edge_weight <= 0:
                    continue

                # Check if this edge is an insider-outsider boundary
                u_is_outsider = u in outsider_indices
                v_is_outsider = v in outsider_indices

                is_boundary_edge = (u_is_outsider != v_is_outsider)
                
                # Heuristic boundary score
                confidence = 0.5
                if is_boundary_edge:
                    confidence += 0.35

                # Attention weighting factor if available
                if attention_weights is not None:
                    # attention_weights shape: (N, N) or (Heads, N, N)
                    if attention_weights.dim() == 3:
                        attn_val = float(attention_weights[:, u, v].mean().item())
                    else:
                        attn_val = float(attention_weights[u, v].item())
                    confidence = min(0.99, confidence + (attn_val * 0.3))

                if confidence >= self.anomaly_threshold or is_boundary_edge:
                    insider_idx = v if u_is_outsider else u
                    outsider_idx = u if u_is_outsider else v
                    ins_name = graph_data.node_names[insider_idx] if graph_data.node_names else f"node_{insider_idx}"
                    out_name = graph_data.node_names[outsider_idx] if graph_data.node_names else f"node_{outsider_idx}"

                    # Infer mechanism
                    mechanism = BridgeMechanism.SOCKS_CHISEL_TUNNEL
                    if "tether" in out_name.lower() or "byod" in out_name.lower():
                        mechanism = BridgeMechanism.DUAL_HOMED_NIC
                    elif "vm" in out_name.lower() or "shadow" in out_name.lower():
                        mechanism = BridgeMechanism.VMWARE_SHARED_NAT

                    detected.append({
                        "bridge_id": f"bridge-{insider_idx}-{outsider_idx}",
                        "insider_node_idx": insider_idx,
                        "outsider_node_idx": outsider_idx,
                        "insider_name": ins_name,
                        "outsider_name": out_name,
                        "mechanism": mechanism.value,
                        "confidence_score": round(confidence, 3),
                        "direction": f"{ins_name} <-> {out_name}",
                        "severity": "CRITICAL" if confidence > 0.8 else "HIGH",
                        "mitre_technique": "T1090 (Proxy: Internal/External Reverse SOCKS)",
                    })

        return detected
