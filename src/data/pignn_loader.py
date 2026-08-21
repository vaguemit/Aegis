"""
Benchmark Dataset Loader for PIGNN Active Directory Graphs.
Loads the 1,033 preprocessed .pt files containing Adjacency Tensors (361, 361, 16),
Feature Matrices (361, 20), and Attack Path Matrices (361, 361).
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union, Dict, Any
import torch
from torch.utils.data import Dataset, DataLoader

from src.data.schema import NetworkGraphData, NUM_NODE_FEATURES, NUM_EDGE_TYPES


def load_pignn_graph(
    file_path: Union[str, Path],
    target_dim: Optional[int] = None
) -> NetworkGraphData:
    """
    Loads a single preprocessed graph .pt file into a NetworkGraphData container.

    Args:
        file_path: Path to the .pt file.
        target_dim: Optional feature dimension to pad to (e.g. 20).

    Returns:
        NetworkGraphData instance containing x_matrix, adj_tensor, y_matrix,
        source_idx, and target_idx.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Graph file not found: {file_path}")

    raw_data = torch.load(path_obj, weights_only=False)
    adj_tensor = raw_data["adj_tensor"].float()    # Shape: (N, N, 16)
    x_matrix = raw_data["X_matrix"].float()        # Shape: (N, feature_dim)
    y_matrix = raw_data["Y_matrix"].float()        # Shape: (N, N)

    if target_dim is not None and x_matrix.shape[1] < target_dim:
        pad = torch.zeros((x_matrix.shape[0], target_dim - x_matrix.shape[1]), dtype=x_matrix.dtype)
        x_matrix = torch.cat([x_matrix, pad], dim=-1)

    graph_id = path_obj.stem
    num_nodes = x_matrix.shape[0]

    return NetworkGraphData(
        graph_id=graph_id,
        num_nodes=num_nodes,
        x_matrix=x_matrix,
        adj_tensor=adj_tensor,
        y_matrix=y_matrix,
    )


class PIGNNDataset(Dataset):
    """
    PyTorch Dataset wrapper for the benchmark enterprise graph collection.
    Supports in-memory caching and lazy on-demand loading.
    """

    def __init__(
        self,
        data_dir: Union[str, Path] = "data/_data_",
        preload: bool = False,
        max_samples: Optional[int] = None,
        pad_to_dim: Optional[int] = 20,
    ):
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            # Fallback search in replication_pkg or current dir
            alt_path = Path("replication_pkg/Physics-Informed-GNN (PIGNN)/_Preprocessing_/_data_")
            if alt_path.exists():
                self.data_dir = alt_path

        self.file_paths: List[Path] = sorted(
            [f for f in self.data_dir.glob("*.pt")]
        )
        if max_samples is not None and max_samples > 0:
            self.file_paths = self.file_paths[:max_samples]

        self.preload = preload
        self.pad_to_dim = pad_to_dim
        self._cache: Dict[int, NetworkGraphData] = {}

        if self.preload:
            for idx in range(len(self.file_paths)):
                self._cache[idx] = load_pignn_graph(self.file_paths[idx], target_dim=self.pad_to_dim)

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            Tuple of (adj_tensor, x_matrix, y_matrix)
            adj_tensor: (N, N, 16)
            x_matrix:   (N, 20)
            y_matrix:   (N, N)
        """
        if idx in self._cache:
            graph_data = self._cache[idx]
        else:
            graph_data = load_pignn_graph(self.file_paths[idx], target_dim=self.pad_to_dim)

        return graph_data.adj_tensor, graph_data.x_matrix, graph_data.y_matrix

    def get_graph(self, idx: int) -> NetworkGraphData:
        """Retrieves the full NetworkGraphData object at index."""
        if idx in self._cache:
            return self._cache[idx]
        return load_pignn_graph(self.file_paths[idx], target_dim=self.pad_to_dim)

    def get_statistics(self) -> Dict[str, Any]:
        """Computes summary statistics across the dataset."""
        total_graphs = len(self.file_paths)
        if total_graphs == 0:
            return {"total_graphs": 0}

        sample = self.get_graph(0)
        sample_path_lens = []
        sample_edge_counts = []

        # Sample up to 50 graphs for quick statistics
        num_sample = min(50, total_graphs)
        for i in range(num_sample):
            g = self.get_graph(i)
            sample_edge_counts.append(int((g.adj_tensor.sum(dim=-1) > 0).sum().item()))
            if g.attack_path_nodes:
                sample_path_lens.append(len(g.attack_path_nodes) - 1)

        avg_path_len = sum(sample_path_lens) / max(1, len(sample_path_lens))
        avg_edges = sum(sample_edge_counts) / max(1, len(sample_edge_counts))

        return {
            "total_graphs": total_graphs,
            "nodes_per_graph": sample.num_nodes,
            "feature_dim": NUM_NODE_FEATURES,
            "num_edge_types": NUM_EDGE_TYPES,
            "avg_edges_per_graph": avg_edges,
            "avg_attack_path_length": avg_path_len,
        }


def create_pignn_dataloader(
    dataset: PIGNNDataset,
    batch_size: int = 16,
    shuffle: bool = True,
    seed: int = 42,
) -> DataLoader:
    """Creates a deterministic PyTorch DataLoader for batched training."""
    generator = torch.Generator()
    generator.manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
    )
