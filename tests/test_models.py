"""
Unit Tests for AegisPath Model Zoo.
Validates forward/backward passes, probability bounds, loss functions,
and attention extractions across all 7 models.
"""

import pytest
import torch
import torch.nn.functional as F

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.losses import (
    FocalEdgeLoss,
    WeightedMaskedBCELoss,
    DegreePenaltyLoss,
    CycleSuppressionLoss,
)
from src.models.baselines import (
    DijkstraShortestPathBaseline,
    CVSSWeightedShortestPathBaseline,
    BiasedRandomWalkBaseline,
    Node2VecBaseline,
)
from src.models.gcn import GCNModel
from src.models.graphsage import GraphSAGEModel
from src.models.gat import GATModel


@pytest.fixture
def sample_graph():
    """Generates a small test graph for model unit testing."""
    generator = SyntheticEnterpriseGenerator(
        num_computers=15, num_servers=3, num_users=20, num_ous=2, seed=42
    )
    return generator.generate()


class TestLosses:
    def test_focal_edge_loss(self, sample_graph):
        loss_fn = FocalEdgeLoss()
        pred = torch.rand_like(sample_graph.y_matrix)
        target = sample_graph.y_matrix
        loss = loss_fn(pred, target)
        assert loss.item() >= 0.0
        assert not torch.isnan(loss)

    def test_weighted_masked_bce_loss(self, sample_graph):
        loss_fn = WeightedMaskedBCELoss(pos_weight=100.0)
        pred = torch.rand_like(sample_graph.y_matrix)
        target = sample_graph.y_matrix
        loss = loss_fn(pred, target)
        assert loss.item() >= 0.0
        assert not torch.isnan(loss)

    def test_degree_and_cycle_losses(self, sample_graph):
        deg_fn = DegreePenaltyLoss(weight=0.1)
        cycle_fn = CycleSuppressionLoss(weight=0.05)

        pred = torch.sigmoid(torch.randn(1, 30, 30))
        deg_loss = deg_fn(pred)
        cycle_loss = cycle_fn(pred)

        assert deg_loss.item() >= 0.0
        assert cycle_loss.item() >= 0.0


class TestBaselines:
    def test_dijkstra_baseline(self, sample_graph):
        baseline = DijkstraShortestPathBaseline()
        path = baseline.predict_path(
            sample_graph.adj_tensor,
            sample_graph.source_idx,
            sample_graph.target_idx,
        )
        assert len(path) >= 1
        assert path[0] == sample_graph.source_idx
        if len(path) > 1:
            assert path[-1] == sample_graph.target_idx

        prob_mat = baseline.predict_edge_probs(
            sample_graph.adj_tensor,
            sample_graph.source_idx,
            sample_graph.target_idx,
        )
        assert prob_mat.shape == (sample_graph.num_nodes, sample_graph.num_nodes)

    def test_cvss_weighted_baseline(self, sample_graph):
        baseline = CVSSWeightedShortestPathBaseline()
        path = baseline.predict_path(
            sample_graph.adj_tensor,
            sample_graph.x_matrix,
            sample_graph.source_idx,
            sample_graph.target_idx,
        )
        assert len(path) >= 1

    def test_biased_random_walk_baseline(self, sample_graph):
        baseline = BiasedRandomWalkBaseline(num_walks=20, max_steps=15)
        probs = baseline.predict_edge_probs(
            sample_graph.adj_tensor,
            sample_graph.x_matrix,
            sample_graph.source_idx,
            sample_graph.target_idx,
        )
        assert probs.shape == (sample_graph.num_nodes, sample_graph.num_nodes)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

    def test_node2vec_baseline(self, sample_graph):
        model = Node2VecBaseline(num_nodes=sample_graph.num_nodes, in_features=20, embedding_dim=32)
        probs = model(sample_graph.x_matrix, sample_graph.adj_tensor)

        assert probs.shape == (sample_graph.num_nodes, sample_graph.num_nodes)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

        # Check backward pass
        loss = probs.sum()
        loss.backward()


class TestGNNModels:
    def test_gcn_model(self, sample_graph):
        model = GCNModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
        probs = model(sample_graph.x_matrix, sample_graph.adj_tensor)

        assert probs.shape == (sample_graph.num_nodes, sample_graph.num_nodes)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

        # Backward pass gradient check
        loss = F.binary_cross_entropy(probs, sample_graph.y_matrix)
        loss.backward()

    def test_graphsage_model(self, sample_graph):
        model = GraphSAGEModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
        probs = model(sample_graph.x_matrix, sample_graph.adj_tensor)

        assert probs.shape == (sample_graph.num_nodes, sample_graph.num_nodes)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

        loss = F.binary_cross_entropy(probs, sample_graph.y_matrix)
        loss.backward()

    def test_gat_primary_model(self, sample_graph):
        model = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
        probs = model(sample_graph.x_matrix, sample_graph.adj_tensor, return_attention=True)

        assert probs.shape == (sample_graph.num_nodes, sample_graph.num_nodes)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

        # Verify attention extraction for explainability
        attn_list = model.get_attention_weights()
        assert len(attn_list) == 2 # 2 layers
        # Attention shape: (B, num_heads, N, N)
        assert attn_list[0].shape[-2:] == (sample_graph.num_nodes, sample_graph.num_nodes)

        loss = F.binary_cross_entropy(probs, sample_graph.y_matrix)
        loss.backward()
