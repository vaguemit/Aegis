"""
Unit Tests for AegisPath Data Engine.
Verifies schema definitions, benchmark loader, synthetic generation,
PyG tensor transformations, and dataset splitting.
"""

import pytest
import torch

from src.data.schema import (
    EntityType,
    EdgeType,
    SecurityProperty,
    OperatingSystem,
    NetworkNode,
    NetworkGraphData,
    NUM_NODE_FEATURES,
    NUM_EDGE_TYPES,
)
from src.data.pignn_loader import PIGNNDataset, load_pignn_graph
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.data.preprocessor import (
    GraphSplitter,
    dense_to_pyg_data,
    create_edge_index_from_tensor,
    sample_negative_edges,
)


class TestSchema:
    def test_feature_dimensions(self):
        """Ensures standardized constants match the 20-dim feature vector and 16 edge types."""
        assert NUM_NODE_FEATURES == 20
        assert NUM_EDGE_TYPES == 16

    def test_node_to_feature_vector(self):
        """Verifies one-hot and boolean encoding into 20-dim tensor."""
        node = NetworkNode(
            node_id=0,
            name="DC01.CORP.LOCAL",
            entity_type=EntityType.COMPUTER,
            os=OperatingSystem.WIN_SERVER_2016_2019,
            is_enabled=True,
            has_spn=False,
            is_high_value=True,
            is_vulnerable=False,
            is_target=True,
            is_owned=False,
        )
        vec = node.to_feature_vector()
        assert vec.shape == (20,)
        assert vec[0] == 1.0 # EntityType.COMPUTER
        assert vec[6] == 1.0 # enabled
        assert vec[8] == 1.0 # highvalue
        assert vec[10] == 1.0 # target


class TestSyntheticGenerator:
    def test_generate_network_graph(self):
        """Tests parametric generation of an enterprise network graph."""
        generator = SyntheticEnterpriseGenerator(
            num_computers=20,
            num_servers=5,
            num_users=40,
            num_ous=3,
            num_gpos=2,
            num_domain_controllers=1,
            seed=42,
        )
        graph_data = generator.generate(scenario_name="test_scenario")

        assert isinstance(graph_data, NetworkGraphData)
        assert graph_data.num_nodes > 0
        assert graph_data.x_matrix.shape == (graph_data.num_nodes, 20)
        assert graph_data.adj_tensor.shape == (graph_data.num_nodes, graph_data.num_nodes, 16)
        assert graph_data.y_matrix.shape == (graph_data.num_nodes, graph_data.num_nodes)
        assert graph_data.source_idx is not None
        assert graph_data.target_idx is not None
        assert len(graph_data.attack_path_nodes) >= 2


class TestPIGNNLoader:
    def test_load_single_benchmark_graph(self):
        """Tests loading of extracted benchmark .pt graphs."""
        dataset = PIGNNDataset(data_dir="data/_data_", max_samples=5)
        if len(dataset) > 0:
            adj_tensor, x_matrix, y_matrix = dataset[0]
            assert adj_tensor.shape == (361, 361, 16)
            assert x_matrix.shape == (361, 20)
            assert y_matrix.shape == (361, 361)

            stats = dataset.get_statistics()
            assert stats["nodes_per_graph"] == 361
            assert stats["feature_dim"] == 20
            assert stats["num_edge_types"] == 16


class TestPreprocessor:
    def test_dense_to_pyg_data(self):
        """Verifies sparse PyG conversion from dense tensors."""
        generator = SyntheticEnterpriseGenerator(
            num_computers=10, num_servers=2, num_users=15, seed=123
        )
        graph_data = generator.generate()
        pyg_data = dense_to_pyg_data(graph_data)

        assert "x" in pyg_data
        assert "edge_index" in pyg_data
        assert "edge_attr" in pyg_data
        assert "edge_label" in pyg_data
        assert pyg_data["x"].shape == (graph_data.num_nodes, 20)
        assert pyg_data["edge_index"].shape[0] == 2
        assert pyg_data["edge_attr"].shape[0] == pyg_data["edge_index"].shape[1]

    def test_graph_splitter(self):
        """Verifies zero data leakage graph-level split."""
        generator = SyntheticEnterpriseGenerator(num_computers=5, seed=42)
        mock_dataset = [generator.generate() for _ in range(20)]

        splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
        train_set, val_set, test_set = splitter.split(mock_dataset)

        assert len(train_set) == 16
        assert len(val_set) == 2
        assert len(test_set) == 2

    def test_sample_negative_edges(self):
        """Verifies negative edge pair extraction."""
        generator = SyntheticEnterpriseGenerator(num_computers=10, seed=42)
        g = generator.generate()
        neg_src, neg_dst = sample_negative_edges(g.y_matrix, g.adj_tensor, num_negatives=50)

        assert neg_src.shape == (50,)
        assert neg_dst.shape == (50,)
        # Ensure none of the sampled negatives are attack edges
        assert (g.y_matrix[neg_src, neg_dst] == 1.0).sum().item() == 0

    def test_data_leakage_audit(self):
        """Verifies that split partitions have 0% graph ID overlap."""
        from src.evaluation.data_leakage_check import audit_graph_splits_for_leakage

        generator = SyntheticEnterpriseGenerator(num_computers=5, seed=42)
        mock_dataset = [generator.generate(scenario_name=f"audit_net_{i}") for i in range(15)]
        splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
        train_set, val_set, test_set = splitter.split(mock_dataset)

        train_ids = [mock_dataset[i].graph_id for i in train_set.indices]
        val_ids = [mock_dataset[i].graph_id for i in val_set.indices]
        test_ids = [mock_dataset[i].graph_id for i in test_set.indices]

        is_clean, msg = audit_graph_splits_for_leakage(train_ids, val_ids, test_ids)
        assert is_clean
        assert "PASSED" in msg
