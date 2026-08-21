"""
Unit Tests for Explainability Engine and Counterfactual Defense Simulator.
Verifies attention attribution, patch simulations, delta risk calculations,
and automated mitigation recommendations.
"""

import pytest
import torch

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.search.beam_search import ConstrainedBeamSearch
from src.analysis.explainability import GATExplainer, PathExplanation, EdgeExplanation
from src.analysis.counterfactual import (
    CounterfactualDefenseEngine,
    CounterfactualResult,
    DefenseActionType,
)


@pytest.fixture
def test_network():
    generator = SyntheticEnterpriseGenerator(
        num_computers=15, num_servers=4, num_users=20, num_ous=2, seed=42
    )
    return generator.generate()


@pytest.fixture
def gat_model():
    return GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)


class TestExplainability:
    def test_explain_edge(self, test_network, gat_model):
        explainer = GATExplainer(gat_model)
        u = test_network.source_idx
        v = test_network.attack_path_nodes[1] if len(test_network.attack_path_nodes) > 1 else 0

        edge_exp = explainer.explain_edge(
            source_idx=u,
            target_idx=v,
            x_matrix=test_network.x_matrix,
            adj_tensor=test_network.adj_tensor,
            node_names=test_network.node_names,
        )

        assert isinstance(edge_exp, EdgeExplanation)
        assert edge_exp.source_idx == u
        assert edge_exp.target_idx == v
        assert len(edge_exp.summary) > 0
        assert len(edge_exp.top_contributing_features) > 0

    def test_explain_path(self, test_network, gat_model):
        explainer = GATExplainer(gat_model)
        path_exp = explainer.explain_path(
            path_nodes=test_network.attack_path_nodes,
            x_matrix=test_network.x_matrix,
            adj_tensor=test_network.adj_tensor,
            node_names=test_network.node_names,
        )

        assert isinstance(path_exp, PathExplanation)
        assert len(path_exp.edge_explanations) == len(test_network.attack_path_nodes) - 1
        assert len(path_exp.key_findings) >= 2


class TestCounterfactualDefense:
    def test_simulate_patch_vulnerability(self, test_network, gat_model):
        defense_engine = CounterfactualDefenseEngine(gat_model)
        # Choose intermediate vulnerable server to patch
        pivot_node = test_network.attack_path_nodes[2] if len(test_network.attack_path_nodes) > 2 else 0

        result = defense_engine.simulate_patch_vulnerability(
            x_matrix=test_network.x_matrix,
            adj_tensor=test_network.adj_tensor,
            node_idx=pivot_node,
            source_idx=test_network.source_idx,
            target_idx=test_network.target_idx,
            node_names=test_network.node_names,
        )

        assert isinstance(result, CounterfactualResult)
        assert result.action_type == DefenseActionType.PATCH_VULNERABILITY
        assert result.original_risk_score >= 0.0
        assert result.mitigated_risk_score >= 0.0
        assert len(result.recommendation_verdict) > 0

    def test_recommend_optimal_defenses(self, test_network, gat_model):
        beam_searcher = ConstrainedBeamSearch(beam_width=2)
        defense_engine = CounterfactualDefenseEngine(gat_model, beam_searcher=beam_searcher)

        with torch.no_grad():
            probs = gat_model(test_network.x_matrix, test_network.adj_tensor)
        paths = beam_searcher.search(
            edge_probs=probs,
            adj_tensor=test_network.adj_tensor,
            x_matrix=test_network.x_matrix,
            source_idx=test_network.source_idx,
            target_idx=test_network.target_idx,
            node_names=test_network.node_names,
            top_k=1,
        )

        recommendations = defense_engine.recommend_optimal_defenses(
            x_matrix=test_network.x_matrix,
            adj_tensor=test_network.adj_tensor,
            predicted_path=paths[0],
            source_idx=test_network.source_idx,
            target_idx=test_network.target_idx,
            node_names=test_network.node_names,
            top_n=3,
        )

        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, CounterfactualResult)
