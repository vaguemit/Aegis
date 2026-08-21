"""
Unit Tests for Advanced XAI (Multi-Head Attention Decomposition & Integrated Gradients).
"""

import pytest
import torch

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.analysis.advanced_xai import AdvancedXAIAnalyzer, AdvancedEdgeExplanation
from src.analysis.mitre_mapper import MitreAttackMapper


@pytest.fixture
def sample_network():
    gen = SyntheticEnterpriseGenerator(num_computers=10, num_servers=3, num_users=15, seed=123)
    return gen.generate()


class TestAdvancedXAI:
    def test_mitre_mapping(self):
        ttp = MitreAttackMapper.get_mitre_mapping("AdminTo")
        assert ttp.tactic_id == "TA0004"
        assert ttp.technique_id == "T1078"

        ttp_rdp = MitreAttackMapper.get_mitre_mapping("CanRDP")
        assert ttp_rdp.technique_id == "T1021"

    def test_multi_head_attention_and_ig(self, sample_network):
        gat = GATModel(in_features=20, hidden_dim=32, out_dim=32, num_heads=4, num_layers=2)
        analyzer = AdvancedXAIAnalyzer(gat)

        u = sample_network.attack_path_nodes[0]
        v = sample_network.attack_path_nodes[1]

        explanation = analyzer.explain_edge_comprehensively(
            u_idx=u,
            v_idx=v,
            x_matrix=sample_network.x_matrix,
            adj_tensor=sample_network.adj_tensor,
            node_names=sample_network.node_names,
        )

        assert isinstance(explanation, AdvancedEdgeExplanation)
        assert len(explanation.head_attentions) == 4
        assert len(explanation.integrated_gradient_saliency) > 0
        assert explanation.mitre_ttp.technique_id is not None
        assert explanation.subgraph_importance_score >= 0.0
