"""
Graph Preprocessing, Tensor Conversions, and Dataset Splitting.
Provides utilities to transform dense adjacency tensors into sparse edge representations,
perform strict graph-level train/val/test splits, and extract negative training pairs.
"""

from typing import List, Tuple, Dict, Optional, Union
import numpy as np
import torch
from torch.utils.data import Dataset, Subset

from src.data.schema import NetworkGraphData, NUM_EDGE_TYPES, NUM_NODE_FEATURES


def create_edge_index_from_tensor(
    adj_tensor: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Extracts sparse edge_index and multi-relational edge_attr from a 3D adjacency tensor.

    Args:
        adj_tensor: Shape (N, N, num_edge_types)

    Returns:
        edge_index: LongTensor of shape (2, E)
        edge_attr: LongTensor of shape (E,) representing the edge relationship type index (0..15)
    """
    num_nodes = adj_tensor.shape[0]
    num_edge_types = adj_tensor.shape[2]

    # Non-zero entries across all channels
    non_zero_coords = (adj_tensor > 0.5).nonzero(as_tuple=False) # (E, 3): [src, dst, edge_type_idx]

    if non_zero_coords.shape[0] == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0,), dtype=torch.long)
        return edge_index, edge_attr

    src = non_zero_coords[:, 0]
    dst = non_zero_coords[:, 1]
    edge_type = non_zero_coords[:, 2]

    edge_index = torch.stack([src, dst], dim=0) # (2, E)
    edge_attr = edge_type.long() # (E,)

    return edge_index, edge_attr


def dense_to_pyg_data(
    graph_data: Union[NetworkGraphData, Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]
) -> Dict[str, torch.Tensor]:
    """
    Transforms dense graph representations into standard sparse GNN dictionary tensors.

    Args:
        graph_data: NetworkGraphData object or (adj_tensor, x_matrix, y_matrix) tuple.

    Returns:
        Dictionary with:
            - 'x': (N, 20) float tensor
            - 'edge_index': (2, E) long tensor
            - 'edge_attr': (E,) long tensor of edge types
            - 'edge_label': (E,) float tensor (1.0 if on attack path, 0.0 otherwise)
            - 'adj_tensor': (N, N, 16) original dense tensor
            - 'y_matrix': (N, N) binary path matrix
    """
    if isinstance(graph_data, NetworkGraphData):
        adj_tensor = graph_data.adj_tensor
        x_matrix = graph_data.x_matrix
        y_matrix = graph_data.y_matrix
    else:
        adj_tensor, x_matrix, y_matrix = graph_data

    edge_index, edge_attr = create_edge_index_from_tensor(adj_tensor)

    # Extract edge labels for existing edges
    if edge_index.shape[1] > 0:
        src = edge_index[0]
        dst = edge_index[1]
        edge_label = y_matrix[src, dst].float()
    else:
        edge_label = torch.empty((0,), dtype=torch.float32)

    return {
        "x": x_matrix.float(),
        "edge_index": edge_index.long(),
        "edge_attr": edge_attr.long(),
        "edge_label": edge_label,
        "adj_tensor": adj_tensor.float(),
        "y_matrix": y_matrix.float(),
    }


class GraphSplitter:
    """
    Strict graph-level dataset splitter.
    Guarantees zero data leakage across train, validation, and test network topologies.
    """

    def __init__(
        self,
        train_ratio: float = 0.80,
        val_ratio: float = 0.10,
        test_ratio: float = 0.10,
        seed: int = 42,
    ):
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Split ratios must sum to 1.0"
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def split(self, dataset: Dataset) -> Tuple[Subset, Subset, Subset]:
        """
        Splits a Dataset into (train_subset, val_subset, test_subset) at the graph level.
        """
        total_len = len(dataset)
        indices = np.arange(total_len)
        rng = np.random.RandomState(self.seed)
        rng.shuffle(indices)

        train_end = int(self.train_ratio * total_len)
        val_end = train_end + int(self.val_ratio * total_len)

        train_idx = indices[:train_end].tolist()
        val_idx = indices[train_end:val_end].tolist()
        test_idx = indices[val_end:].tolist()

        return (
            Subset(dataset, train_idx),
            Subset(dataset, val_idx),
            Subset(dataset, test_idx),
        )


def sample_negative_edges(
    y_matrix: torch.Tensor,
    adj_tensor: torch.Tensor,
    num_negatives: int,
    hard_ratio: float = 0.5,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Samples negative edge pairs (u, v) where y_matrix[u, v] == 0.
    Combines hard negatives (edges that exist in adj_tensor but are NOT part of the attack)
    with easy random negatives (pairs that do not share direct connections).

    Args:
        y_matrix: (N, N) binary attack path indicator.
        adj_tensor: (N, N, 16) existing edge tensor.
        num_negatives: Total number of negative pairs to return.
        hard_ratio: Fraction of negatives chosen from existing network links.

    Returns:
        neg_src: (num_negatives,) LongTensor
        neg_dst: (num_negatives,) LongTensor
    """
    num_nodes = y_matrix.shape[0]
    existing_edges = (adj_tensor.sum(dim=-1) > 0.5) & (y_matrix < 0.5)
    hard_coords = existing_edges.nonzero(as_tuple=False)

    num_hard = int(num_negatives * hard_ratio)
    num_rand = num_negatives - num_hard

    selected_src = []
    selected_dst = []

    # 1. Hard negatives from existing non-attack graph edges
    if hard_coords.shape[0] > 0:
        n_avail = hard_coords.shape[0]
        chosen_indices = torch.randperm(n_avail)[:num_hard]
        selected_src.append(hard_coords[chosen_indices, 0])
        selected_dst.append(hard_coords[chosen_indices, 1])
    else:
        num_rand = num_negatives

    # 2. Random negatives
    while len(selected_src) == 0 or torch.cat(selected_src).shape[0] < num_negatives:
        needed = num_negatives - (torch.cat(selected_src).shape[0] if selected_src else 0)
        rand_u = torch.randint(0, num_nodes, (needed * 2,))
        rand_v = torch.randint(0, num_nodes, (needed * 2,))
        # Filter valid negatives (not self loops, not attack edges)
        valid_mask = (rand_u != rand_v) & (y_matrix[rand_u, rand_v] < 0.5)
        valid_u = rand_u[valid_mask][:needed]
        valid_v = rand_v[valid_mask][:needed]
        selected_src.append(valid_u)
        selected_dst.append(valid_v)

    all_src = torch.cat(selected_src)[:num_negatives]
    all_dst = torch.cat(selected_dst)[:num_negatives]

    return all_src, all_dst
