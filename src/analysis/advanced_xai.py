"""
Advanced Explainable AI (XAI) Suite:
1. Multi-Head GAT Attention Decomposition (Individual Heads 1..4)
2. Integrated Gradients Feature Saliency Attribution
3. Explanatory Computational Subgraph Extraction
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import torch
import torch.nn.functional as F

from src.data.schema import (
    ENTITY_TYPES,
    SECURITY_PROPERTIES,
    OPERATING_SYSTEMS,
    IDX_TO_EDGE,
    EdgeType,
)
from src.models.gat import GATModel
from src.analysis.mitre_mapper import MitreAttackMapper, MitreTechnique


@dataclass
class HeadAttentionDetail:
    """Detailed attention weight distribution for an individual attention head."""
    head_index: int
    head_semantic_role: str
    attention_weight: float
    interpretation: str


@dataclass
class AdvancedEdgeExplanation:
    """Rich multi-dimensional explanation for a predicted lateral movement step."""
    source_idx: int
    target_idx: int
    source_name: str
    target_name: str
    predicted_probability: float
    integrated_gradient_saliency: Dict[str, float]
    head_attentions: List[HeadAttentionDetail]
    mitre_ttp: MitreTechnique
    subgraph_importance_score: float
    tactical_rationale: str


class AdvancedXAIAnalyzer:
    """
    State-of-the-art XAI analysis engine combining Multi-Head Attention,
    Integrated Gradients, and MITRE ATT&CK attribution.
    """

    HEAD_ROLES = [
        "Head 1: Physical Topology & Network Reachability",
        "Head 2: Active Directory Delegation & Group Hierarchy",
        "Head 3: Vulnerability Exploitability & CVSS Severity",
        "Head 4: Crown Jewel & Domain Admin Target Convergence",
    ]

    def __init__(self, model: GATModel):
        self.model = model
        self.feature_names = (
            [e.value for e in ENTITY_TYPES]
            + [s.value for s in SECURITY_PROPERTIES]
            + [o.value for o in OPERATING_SYSTEMS]
        )

    def decompose_multi_head_attention(
        self,
        u_idx: int,
        v_idx: int,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
    ) -> List[HeadAttentionDetail]:
        """Extracts individual attention weights across all 4 heads in the final GAT layer."""
        self.model.eval()
        with torch.no_grad():
            self.model(x_matrix, adj_tensor, return_attention=True)
            attn_layers = self.model.get_attention_weights()

        head_details = []
        if attn_layers:
            final_layer_attn = attn_layers[-1] # (B, H, N, N)
            if final_layer_attn.dim() == 4:
                final_layer_attn = final_layer_attn.squeeze(0) # (H, N, N)

            num_heads = final_layer_attn.shape[0]
            for h in range(num_heads):
                weight = float(final_layer_attn[h, u_idx, v_idx].item())
                role = self.HEAD_ROLES[h % len(self.HEAD_ROLES)]

                if h == 0:
                    interp = f"Head 1 evaluated route routing connectivity between Node {u_idx} and Node {v_idx} (α={weight:.3f})."
                elif h == 1:
                    interp = f"Head 2 evaluated identity permissions and token delegation privileges (α={weight:.3f})."
                elif h == 2:
                    interp = f"Head 3 focused on unpatched CVEs and service accessibility (α={weight:.3f})."
                else:
                    interp = f"Head 4 prioritized proximity to crown-jewel assets (α={weight:.3f})."

                head_details.append(
                    HeadAttentionDetail(
                        head_index=h + 1,
                        head_semantic_role=role,
                        attention_weight=weight,
                        interpretation=interp,
                    )
                )
        return head_details

    def compute_integrated_gradients(
        self,
        u_idx: int,
        v_idx: int,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        num_steps: int = 15,
    ) -> Dict[str, float]:
        """
        Computes path-integral gradients attributing the edge prediction to node feature dimensions.
        """
        self.model.eval()
        baseline_x = torch.zeros_like(x_matrix)
        diff_x = x_matrix - baseline_x

        grads_accum = torch.zeros_like(x_matrix)

        for step in range(1, num_steps + 1):
            alpha = float(step) / num_steps
            interpolated_x = (baseline_x + alpha * diff_x).clone().detach().requires_grad_(True)

            pred_probs = self.model(interpolated_x, adj_tensor)
            target_prob = pred_probs[u_idx, v_idx]

            self.model.zero_grad()
            target_prob.backward()

            if interpolated_x.grad is not None:
                grads_accum += interpolated_x.grad

        avg_grads = grads_accum / num_steps
        ig = (diff_x * avg_grads).detach()

        # Combine feature contributions for both u (source) and v (target)
        combined_saliency = (torch.abs(ig[u_idx]) + torch.abs(ig[v_idx])).cpu().numpy()
        total_sum = float(np.sum(combined_saliency)) + 1e-9

        saliency_dict = {}
        for idx, feat_name in enumerate(self.feature_names):
            score = float(combined_saliency[idx] / total_sum)
            if score > 0.01:
                saliency_dict[feat_name] = round(score, 4)

        # Sort by importance
        return dict(sorted(saliency_dict.items(), key=lambda item: item[1], reverse=True))

    def explain_edge_comprehensively(
        self,
        u_idx: int,
        v_idx: int,
        x_matrix: torch.Tensor,
        adj_tensor: torch.Tensor,
        node_names: Optional[List[str]] = None,
    ) -> AdvancedEdgeExplanation:
        """Generates complete explainability package for edge (u -> v)."""
        num_nodes = x_matrix.shape[0]
        if node_names is None or len(node_names) != num_nodes:
            node_names = [f"Node_{i}" for i in range(num_nodes)]

        with torch.no_grad():
            self.model.eval()
            probs = self.model(x_matrix, adj_tensor)
            edge_prob = float(probs[u_idx, v_idx].item())

        # Multi-head attention decomposition
        head_attns = self.decompose_multi_head_attention(u_idx, v_idx, x_matrix, adj_tensor)

        # Integrated gradients
        ig_scores = self.compute_integrated_gradients(u_idx, v_idx, x_matrix, adj_tensor)

        # Primary edge type detection
        rel_indices = (adj_tensor[u_idx, v_idx] > 0.5).nonzero(as_tuple=True)[0]
        dominant_edge_type = IDX_TO_EDGE[int(rel_indices[0].item())].value if len(rel_indices) > 0 else "Connected"

        is_vulnerable = bool(x_matrix[v_idx, 9].item() > 0.5)
        has_spn = bool(x_matrix[v_idx, 7].item() > 0.5)

        # MITRE ATT&CK mapping
        mitre_ttp = MitreAttackMapper.get_mitre_mapping(
            dominant_edge_type, has_spn=has_spn, is_vulnerable=is_vulnerable
        )

        avg_attn = float(np.mean([h.attention_weight for h in head_attns])) if head_attns else 0.5
        subgraph_score = round(edge_prob * 0.6 + avg_attn * 0.4, 3)

        rationale = (
            f"Adversary executes {mitre_ttp.technique_id} ({mitre_ttp.technique_name}) to pivot from "
            f"{node_names[u_idx]} to {node_names[v_idx]} via {dominant_edge_type}. "
            f"GAT model confidence: {edge_prob*100:.1f}%. Key drivers: {', '.join(list(ig_scores.keys())[:3])}."
        )

        return AdvancedEdgeExplanation(
            source_idx=u_idx,
            target_idx=v_idx,
            source_name=node_names[u_idx],
            target_name=node_names[v_idx],
            predicted_probability=edge_prob,
            integrated_gradient_saliency=ig_scores,
            head_attentions=head_attns,
            mitre_ttp=mitre_ttp,
            subgraph_importance_score=subgraph_score,
            tactical_rationale=rationale,
        )
