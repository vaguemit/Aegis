"""
Unit Tests for Constrained Beam Search and Security Constraint Engine.
Verifies Top-K generation, loop prevention, feasibility checking, and confidence rankings.
"""

import pytest
import torch

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.models.baselines import DijkstraShortestPathBaseline
from src.search.feasibility import SecurityConstraintEngine
from src.search.beam_search import ConstrainedBeamSearch, PredictedAttackPath


@pytest.fixture
def test_network():
    generator = SyntheticEnterpriseGenerator(
        num_computers=20, num_servers=5, num_users=25, num_ous=3, seed=123
    )
    return generator.generate()


class TestSecurityConstraints:
    def test_no_self_loops(self, test_network):
        engine = SecurityConstraintEngine()
        is_valid, reason = engine.is_transition_valid(
            0, 0, test_network.x_matrix, test_network.adj_tensor
        )
        assert not is_valid
        assert "Self loop" in reason

    def test_cycle_prevention(self, test_network):
        engine = SecurityConstraintEngine()
        current_path = [1, 5, 8]
        is_valid, reason = engine.is_transition_valid(
            8, 5, test_network.x_matrix, test_network.adj_tensor, current_path=current_path
        )
        assert not is_valid
        assert "Cycle detected" in reason

    def test_valid_successors(self, test_network):
        engine = SecurityConstraintEngine()
        succs = engine.get_valid_successors(
            test_network.source_idx,
            test_network.x_matrix,
            test_network.adj_tensor,
        )
        assert isinstance(succs, list)
        assert len(succs) > 0


class TestConstrainedBeamSearch:
    def test_top_k_path_search(self, test_network):
        # Generate edge probabilities using GAT
        gat = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
        edge_probs = gat(test_network.x_matrix, test_network.adj_tensor)

        beam_searcher = ConstrainedBeamSearch(beam_width=3, max_hops=10)
        paths = beam_searcher.search(
            edge_probs=edge_probs,
            adj_tensor=test_network.adj_tensor,
            x_matrix=test_network.x_matrix,
            source_idx=test_network.source_idx,
            target_idx=test_network.target_idx,
            node_names=test_network.node_names,
            top_k=3,
        )

        assert len(paths) >= 1
        top_path = paths[0]
        assert isinstance(top_path, PredictedAttackPath)
        assert top_path.nodes[0] == test_network.source_idx
        assert top_path.confidence_score >= 0.0
        assert top_path.rank == 1
        assert len(top_path.node_names) == len(top_path.nodes)

    def test_baseline_shortest_path_beam_search(self, test_network):
        baseline = DijkstraShortestPathBaseline()
        edge_probs = baseline.predict_edge_probs(
            test_network.adj_tensor, test_network.source_idx, test_network.target_idx
        )

        beam_searcher = ConstrainedBeamSearch(beam_width=2, max_hops=10)
        paths = beam_searcher.search(
            edge_probs=edge_probs,
            adj_tensor=test_network.adj_tensor,
            x_matrix=test_network.x_matrix,
            source_idx=test_network.source_idx,
            target_idx=test_network.target_idx,
            node_names=test_network.node_names,
        )

        assert len(paths) >= 1
        assert paths[0].nodes[0] == test_network.source_idx
        if len(paths[0].nodes) > 1:
            assert paths[0].nodes[-1] == test_network.target_idx
