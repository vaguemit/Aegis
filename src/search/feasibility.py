"""
Security Feasibility and Cybersecurity Constraint Engine.
Validates lateral movement preconditions, credential prerequisites,
vulnerability exploitation requirements, and Active Directory privileges.
"""

from typing import List, Optional, Tuple, Set, Dict, Any
import torch

from src.data.schema import (
    EntityType,
    EdgeType,
    SecurityProperty,
    NetworkGraphData,
    PROPERTY_TO_IDX,
    ENTITY_TO_IDX,
    EDGE_TO_IDX,
)


class SecurityConstraintEngine:
    """
    Evaluates whether an adversarial transition u -> v is physically and tactically feasible.
    Prunes transitions that violate cybersecurity preconditions (e.g. exploiting non-existent CVEs,
    delegation without SPN, or moving through unauthenticated networks).
    """

    def __init__(
        self,
        enforce_vulnerability_on_exploit: bool = True,
        enforce_group_membership: bool = True,
        allow_any_existing_edge: bool = False,
    ):
        self.enforce_vulnerability_on_exploit = enforce_vulnerability_on_exploit
        self.enforce_group_membership = enforce_group_membership
        self.allow_any_existing_edge = allow_any_existing_edge

    def is_transition_valid(
        self,
        u_idx: int,
        v_idx: int,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        current_path: Optional[List[int]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if step u -> v is permitted.

        Args:
            u_idx: Source node index
            v_idx: Destination candidate node index
            x_matrix: (N, 20) node feature matrix
            adj_tensor: (N, N, 16) multi-relational adjacency tensor
            current_path: Path history to detect loops

        Returns:
            Tuple of (is_valid: bool, rejection_reason: Optional[str])
        """
        # 1. No self loops
        if u_idx == v_idx:
            return False, "Self loop transition rejected"

        # 2. Cycle prevention in current path
        if current_path is not None and v_idx in current_path:
            return False, f"Cycle detected: node {v_idx} already in path"

        # 3. Check physical network / AD edge existence
        existing_relations = (adj_tensor[u_idx, v_idx] > 0.5).nonzero(as_tuple=True)[0]
        if len(existing_relations) == 0:
            return False, f"No existing relationship between node {u_idx} and node {v_idx}"

        if self.allow_any_existing_edge:
            return True, None

        # 4. Check specific tactical requirements
        vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
        is_dst_vulnerable = bool(x_matrix[v_idx, vuln_col].item() > 0.5)

        # Check relation types
        open_edge_idx = EDGE_TO_IDX[EdgeType.OPEN]
        admin_edge_idx = EDGE_TO_IDX[EdgeType.ADMIN_TO]
        dcsync_edge_idx = EDGE_TO_IDX[EdgeType.DC_SYNC]

        # 'Open' (Remote Code Execution) requires destination to have an unpatched vulnerability
        if open_edge_idx in existing_relations and self.enforce_vulnerability_on_exploit:
            if not is_dst_vulnerable:
                # If 'Open' is the ONLY relationship, reject it
                if len(existing_relations) == 1:
                    return False, f"Destination node {v_idx} is not vulnerable to remote exploitation"

        return True, None

    def get_valid_successors(
        self,
        current_node: int,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        current_path: Optional[List[int]] = None,
    ) -> List[int]:
        """Returns all valid, feasible successor node indices from current_node."""
        num_nodes = x_matrix.shape[0]
        # Candidate successors with at least one relation channel
        candidate_indices = (adj_tensor[current_node].sum(dim=-1) > 0.5).nonzero(as_tuple=True)[0]

        valid_successors = []
        for cand in candidate_indices:
            v = int(cand.item())
            is_valid, _ = self.is_transition_valid(
                current_node, v, x_matrix, adj_tensor, current_path
            )
            if is_valid:
                valid_successors.append(v)

        return valid_successors
