"""
Counterfactual Defense Simulator & Automated Security Decision Support Engine.
Simulates proactive defensive mitigations (patching CVEs, disabling protocols,
revoking privileges, blocking links) on cloned graph states to evaluate delta risk
and attack trajectory rerouting.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Union
import copy
import torch

from src.data.schema import (
    NetworkGraphData,
    EdgeType,
    SecurityProperty,
    PROPERTY_TO_IDX,
    EDGE_TO_IDX,
)
from src.models.gat import GATModel
from src.search.beam_search import ConstrainedBeamSearch, PredictedAttackPath


class DefenseActionType(str, Enum):
    PATCH_VULNERABILITY = "Patch Vulnerability"
    DISABLE_SERVICE = "Disable Service Protocol"
    REVOKE_PRIVILEGE = "Revoke Administrative Privilege"
    BLOCK_COMMUNICATION = "Block Network Communication"


@dataclass
class CounterfactualResult:
    """Detailed outcome of a counterfactual defense simulation."""
    action_type: DefenseActionType
    action_description: str
    target_node_idx: Optional[int]
    target_node_name: Optional[str]
    original_risk_score: float
    mitigated_risk_score: float
    delta_risk: float                          # R_before - R_after (positive is good)
    risk_reduction_pct: float                  # Percentage risk reduction
    original_path: PredictedAttackPath
    mitigated_path: Optional[PredictedAttackPath]
    path_was_diverted: bool
    path_was_severed: bool                     # If attacker cannot reach target anymore
    recommendation_verdict: str


class CounterfactualDefenseEngine:
    """
    Simulates defensive interventions on enterprise graph topologies.
    The original graph is never mutated; all evaluations operate on cloned tensor states.
    """

    def __init__(
        self,
        model: GATModel,
        beam_searcher: Optional[ConstrainedBeamSearch] = None,
    ):
        self.model = model
        self.beam_searcher = beam_searcher or ConstrainedBeamSearch(beam_width=3, max_hops=12)

    def _clone_state(
        self, x_matrix: torch.Tensor, adj_tensor: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns deep copies of graph tensors to guarantee zero side-effects."""
        return x_matrix.clone(), adj_tensor.clone()

    def simulate_patch_vulnerability(
        self,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        node_idx: int,
        source_idx: int,
        target_idx: int,
        node_names: Optional[List[str]] = None,
    ) -> CounterfactualResult:
        """
        Simulates patching a vulnerability on node_idx.
        Sets is_vulnerable = 0 and removes incoming 'Open' remote exploit edges.
        """
        num_nodes = x_matrix.shape[0]
        if node_names is None or len(node_names) != num_nodes:
            node_names = [f"Node_{i}" for i in range(num_nodes)]

        # 1. Baseline prediction before mitigation
        with torch.no_grad():
            self.model.eval()
            orig_probs = self.model(x_matrix, adj_tensor)

        orig_paths = self.beam_searcher.search(
            edge_probs=orig_probs,
            adj_tensor=adj_tensor,
            x_matrix=x_matrix,
            source_idx=source_idx,
            target_idx=target_idx,
            node_names=node_names,
            top_k=1,
        )
        orig_path = orig_paths[0]
        orig_risk = orig_path.confidence_score

        # 2. Clone state and apply patch mitigation
        x_mitigated, adj_mitigated = self._clone_state(x_matrix, adj_tensor)

        # Set is_vulnerable = 0
        vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
        x_mitigated[node_idx, vuln_col] = 0.0

        # Remove incoming 'Open' exploit edges targeting node_idx
        open_idx = EDGE_TO_IDX[EdgeType.OPEN]
        adj_mitigated[:, node_idx, open_idx] = 0.0

        # 3. Re-run GAT on patched network
        with torch.no_grad():
            mit_probs = self.model(x_mitigated, adj_mitigated)

        mit_paths = self.beam_searcher.search(
            edge_probs=mit_probs,
            adj_tensor=adj_mitigated,
            x_matrix=x_mitigated,
            source_idx=source_idx,
            target_idx=target_idx,
            node_names=node_names,
            top_k=1,
        )
        mit_path = mit_paths[0] if mit_paths else None
        mit_risk = mit_path.confidence_score if mit_path else 0.0

        # 4. Compare outcomes
        delta_risk = orig_risk - mit_risk
        reduction_pct = (delta_risk / max(1e-5, orig_risk)) * 100.0

        path_severed = (mit_path is None or (len(mit_path.nodes) > 0 and mit_path.nodes[-1] != target_idx))
        path_diverted = (mit_path is not None and mit_path.nodes != orig_path.nodes)

        verdict = (
            f"Applying security patch on '{node_names[node_idx]}' reduces attack path likelihood "
            f"from {orig_risk*100:.1f}% to {mit_risk*100:.1f}% (ΔRisk: -{reduction_pct:.1f}%)."
        )
        if path_severed:
            verdict += " The critical attack path is completely severed!"
        elif path_diverted:
            verdict += " The adversary is forced to pivot through an alternative, lower-confidence route."

        return CounterfactualResult(
            action_type=DefenseActionType.PATCH_VULNERABILITY,
            action_description=f"Patch software vulnerability (CVE) on {node_names[node_idx]}",
            target_node_idx=node_idx,
            target_node_name=node_names[node_idx],
            original_risk_score=float(orig_risk),
            mitigated_risk_score=float(mit_risk),
            delta_risk=float(delta_risk),
            risk_reduction_pct=float(reduction_pct),
            original_path=orig_path,
            mitigated_path=mit_path,
            path_was_diverted=path_diverted,
            path_was_severed=path_severed,
            recommendation_verdict=verdict,
        )

    def simulate_disable_service(
        self,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        source_idx: int,
        target_idx: int,
        edge_u: int,
        edge_v: int,
        edge_type: EdgeType,
        node_names: Optional[List[str]] = None,
    ) -> CounterfactualResult:
        """Simulates disabling a specific protocol edge (e.g. CanRDP, ExecuteDCOM, AdminTo)."""
        num_nodes = x_matrix.shape[0]
        if node_names is None or len(node_names) != num_nodes:
            node_names = [f"Node_{i}" for i in range(num_nodes)]

        with torch.no_grad():
            self.model.eval()
            orig_probs = self.model(x_matrix, adj_tensor)

        orig_paths = self.beam_searcher.search(
            edge_probs=orig_probs,
            adj_tensor=adj_tensor,
            x_matrix=x_matrix,
            source_idx=source_idx,
            target_idx=target_idx,
            node_names=node_names,
            top_k=1,
        )
        orig_path = orig_paths[0]
        orig_risk = orig_path.confidence_score

        x_mit, adj_mit = self._clone_state(x_matrix, adj_tensor)
        rel_idx = EDGE_TO_IDX[edge_type]
        adj_mit[edge_u, edge_v, rel_idx] = 0.0

        with torch.no_grad():
            mit_probs = self.model(x_mit, adj_mit)

        mit_paths = self.beam_searcher.search(
            edge_probs=mit_probs,
            adj_tensor=adj_mit,
            x_matrix=x_mit,
            source_idx=source_idx,
            target_idx=target_idx,
            node_names=node_names,
            top_k=1,
        )
        mit_path = mit_paths[0] if mit_paths else None
        mit_risk = mit_path.confidence_score if mit_path else 0.0

        delta_risk = orig_risk - mit_risk
        reduction_pct = (delta_risk / max(1e-5, orig_risk)) * 100.0

        return CounterfactualResult(
            action_type=DefenseActionType.DISABLE_SERVICE,
            action_description=f"Disable protocol {edge_type.value} between {node_names[edge_u]} and {node_names[edge_v]}",
            target_node_idx=edge_v,
            target_node_name=node_names[edge_v],
            original_risk_score=float(orig_risk),
            mitigated_risk_score=float(mit_risk),
            delta_risk=float(delta_risk),
            risk_reduction_pct=float(reduction_pct),
            original_path=orig_path,
            mitigated_path=mit_path,
            path_was_diverted=(mit_path is not None and mit_path.nodes != orig_path.nodes),
            path_was_severed=(mit_path is None or mit_path.nodes[-1] != target_idx),
            recommendation_verdict=f"Disabling {edge_type.value} reduces path risk by {reduction_pct:.1f}%.",
        )

    def recommend_optimal_defenses(
        self,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        predicted_path: PredictedAttackPath,
        source_idx: int,
        target_idx: int,
        node_names: Optional[List[str]] = None,
        top_n: int = 3,
    ) -> List[CounterfactualResult]:
        """
        Automated Security Decision Support:
        Iterates over all intermediate nodes along the predicted attack chain, simulates patches
        and protocol closures, and returns the top-N defense actions ranked by maximum risk reduction.
        """
        results: List[CounterfactualResult] = []
        path_nodes = predicted_path.nodes

        # Test patching on all intermediate nodes
        for node in path_nodes[1:-1]:
            vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
            if x_matrix[node, vuln_col] > 0.5:
                res = self.simulate_patch_vulnerability(
                    x_matrix=x_matrix,
                    adj_tensor=adj_tensor,
                    node_idx=node,
                    source_idx=source_idx,
                    target_idx=target_idx,
                    node_names=node_names,
                )
                results.append(res)

        # Test disabling key protocol hops along the path
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            rel_indices = (adj_tensor[u, v] > 0.5).nonzero(as_tuple=True)[0]
            for r in rel_indices:
                edge_type = EdgeType(list(EDGE_TO_IDX.keys())[int(r.item())])
                if edge_type in [EdgeType.OPEN, EdgeType.CAN_RDP, EdgeType.ADMIN_TO, EdgeType.EXECUTE_DCOM]:
                    res = self.simulate_disable_service(
                        x_matrix=x_matrix,
                        adj_tensor=adj_tensor,
                        source_idx=source_idx,
                        target_idx=target_idx,
                        edge_u=u,
                        edge_v=v,
                        edge_type=edge_type,
                        node_names=node_names,
                    )
                    results.append(res)

        # Sort by maximum delta risk
        results.sort(key=lambda r: r.delta_risk, reverse=True)
        return results[:top_n]
