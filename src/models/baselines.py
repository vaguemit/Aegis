"""
Classical & Embedding Baselines for Attack Path Prediction.
Implements:
1. Dijkstra Shortest Path
2. CVSS-Weighted Shortest Path
3. Biased Random Walk
4. Node2Vec Graph Embeddings + Link Classifier
"""

import math
import random
from typing import List, Optional, Tuple, Dict, Any, Union
import networkx as nx
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.data.schema import NetworkGraphData, PROPERTY_TO_IDX, SecurityProperty


class DijkstraShortestPathBaseline:
    """
    Baseline 1: Unweighted Shortest Path.
    Computes shortest topological distance between source and target on the aggregated graph.
    """

    def __init__(self):
        self.name = "Dijkstra_ShortestPath"

    def predict_path(
        self,
        adj_tensor: torch.Tensor,
        source_idx: int,
        target_idx: int,
    ) -> List[int]:
        """
        Args:
            adj_tensor: (N, N, 16) or (N, N)
            source_idx: Start node
            target_idx: Goal node
        """
        if adj_tensor.dim() == 3:
            binary_adj = (adj_tensor.sum(dim=-1) > 0.5).cpu().numpy()
        else:
            binary_adj = (adj_tensor > 0.5).cpu().numpy()

        G = nx.from_numpy_array(binary_adj, create_using=nx.DiGraph)
        try:
            path = nx.shortest_path(G, source=source_idx, target=target_idx)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [source_idx]

    def predict_edge_probs(
        self,
        adj_tensor: torch.Tensor,
        source_idx: int,
        target_idx: int,
    ) -> torch.Tensor:
        """Returns binary (N, N) matrix representing predicted shortest path edges."""
        num_nodes = adj_tensor.shape[0]
        prob_matrix = torch.zeros((num_nodes, num_nodes), dtype=torch.float32)
        path = self.predict_path(adj_tensor, source_idx, target_idx)
        for i in range(len(path) - 1):
            prob_matrix[path[i], path[i + 1]] = 1.0
        return prob_matrix


class CVSSWeightedShortestPathBaseline:
    """
    Baseline 2: CVSS / Vulnerability-Weighted Path.
    Weights each edge inversely by the vulnerability & privilege state of the target node.
    High-vulnerability nodes have low traversal cost, modeling attacker preference.
    """

    def __init__(self, vuln_discount: float = 0.25, base_weight: float = 1.0):
        self.name = "CVSS_Weighted_Path"
        self.vuln_discount = vuln_discount
        self.base_weight = base_weight

    def predict_path(
        self,
        adj_tensor: torch.Tensor,
        x_matrix: torch.Tensor,
        source_idx: int,
        target_idx: int,
    ) -> List[int]:
        num_nodes = x_matrix.shape[0]
        if adj_tensor.dim() == 3:
            binary_adj = (adj_tensor.sum(dim=-1) > 0.5).cpu().numpy()
        else:
            binary_adj = (adj_tensor > 0.5).cpu().numpy()

        vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
        is_vuln = (x_matrix[:, vuln_col] > 0.5).cpu().numpy()

        G = nx.DiGraph()
        for u in range(num_nodes):
            for v in range(num_nodes):
                if binary_adj[u, v]:
                    # Lower cost for transitioning to vulnerable or critical nodes
                    cost = self.base_weight
                    if is_vuln[v]:
                        cost *= self.vuln_discount
                    G.add_edge(u, v, weight=cost)

        try:
            path = nx.dijkstra_path(G, source=source_idx, target=target_idx, weight="weight")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [source_idx]

    def predict_edge_probs(
        self,
        adj_tensor: torch.Tensor,
        x_matrix: torch.Tensor,
        source_idx: int,
        target_idx: int,
    ) -> torch.Tensor:
        num_nodes = x_matrix.shape[0]
        prob_matrix = torch.zeros((num_nodes, num_nodes), dtype=torch.float32)
        path = self.predict_path(adj_tensor, x_matrix, source_idx, target_idx)
        for i in range(len(path) - 1):
            prob_matrix[path[i], path[i + 1]] = 1.0
        return prob_matrix


class BiasedRandomWalkBaseline:
    """
    Baseline 3: Vulnerability & Degree-Biased Random Walk.
    Simulates probabilistic attacker exploration biased towards vulnerable neighbors.
    """

    def __init__(self, num_walks: int = 100, max_steps: int = 20, vuln_bias: float = 3.0):
        self.name = "Biased_Random_Walk"
        self.num_walks = num_walks
        self.max_steps = max_steps
        self.vuln_bias = vuln_bias

    def predict_edge_probs(
        self,
        adj_tensor: torch.Tensor,
        x_matrix: torch.Tensor,
        source_idx: int,
        target_idx: int,
    ) -> torch.Tensor:
        num_nodes = x_matrix.shape[0]
        if adj_tensor.dim() == 3:
            binary_adj = (adj_tensor.sum(dim=-1) > 0.5).cpu().numpy()
        else:
            binary_adj = (adj_tensor > 0.5).cpu().numpy()

        vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
        is_vuln = (x_matrix[:, vuln_col] > 0.5).cpu().numpy()

        edge_visit_counts = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        success_walks = 0

        for _ in range(self.num_walks):
            current = source_idx
            walk_edges = []
            visited = {current}

            for _ in range(self.max_steps):
                if current == target_idx:
                    success_walks += 1
                    for (u, v) in walk_edges:
                        edge_visit_counts[u, v] += 1.0
                    break

                neighbors = np.where(binary_adj[current])[0]
                unvisited = [n for n in neighbors if n not in visited]
                if not unvisited:
                    break

                # Compute transition probabilities biased by vulnerability
                weights = [self.vuln_bias if is_vuln[n] else 1.0 for n in unvisited]
                prob = np.array(weights, dtype=np.float32)
                prob /= prob.sum()

                next_node = np.random.choice(unvisited, p=prob)
                walk_edges.append((current, next_node))
                visited.add(next_node)
                current = next_node

        if success_walks > 0:
            edge_probs = edge_visit_counts / float(success_walks)
        else:
            # Fallback to shortest path if no random walk reached target
            shortest_path = DijkstraShortestPathBaseline().predict_path(adj_tensor, source_idx, target_idx)
            edge_probs = np.zeros((num_nodes, num_nodes), dtype=np.float32)
            for i in range(len(shortest_path) - 1):
                edge_probs[shortest_path[i], shortest_path[i + 1]] = 1.0

        return torch.from_numpy(edge_probs).float()


class Node2VecBaseline(nn.Module):
    """
    Baseline 4: Node2Vec Graph Embeddings + Multi-Layer Perceptron Link Predictor.
    Generates random-walk neighborhood embeddings and classifies candidate edges.
    """

    def __init__(
        self,
        num_nodes: int = 361,
        in_features: int = 20,
        embedding_dim: int = 64,
        hidden_dim: int = 64,
    ):
        super().__init__()
        self.name = "Node2Vec_Classifier"
        self.num_nodes = num_nodes
        self.embedding_dim = embedding_dim
        # Node structural embedding lookup table
        self.node_embed = nn.Embedding(num_nodes, embedding_dim)
        # Feature projection
        self.feat_proj = nn.Linear(in_features, embedding_dim)
        # Edge classifier MLP: takes [embed_u || embed_v || feat_u || feat_v]
        self.edge_mlp = nn.Sequential(
            nn.Linear(embedding_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        x: torch.Tensor,
        adj_tensor: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            x: Node features (B, N, F) or (N, F)
            adj_tensor: Adjacency tensor (B, N, N, E) or (N, N, E)

        Returns:
            Edge attack likelihood matrix of shape (B, N, N) or (N, N)
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, feat_dim = x.shape
        node_indices = torch.arange(num_nodes, device=x.device).unsqueeze(0).expand(batch_size, -1)

        # Structural + attribute embeddings
        struct_embed = self.node_embed(node_indices) # (B, N, D)
        attr_embed = self.feat_proj(x)                # (B, N, D)
        combined_embed = torch.cat([struct_embed, attr_embed], dim=-1) # (B, N, 2D)

        # Compute pair representations: (B, N, N, 4D)
        embed_u = combined_embed.unsqueeze(2).expand(-1, -1, num_nodes, -1)
        embed_v = combined_embed.unsqueeze(1).expand(-1, num_nodes, -1, -1)
        pair_feat = torch.cat([embed_u, embed_v], dim=-1)

        edge_probs = self.edge_mlp(pair_feat).squeeze(-1) # (B, N, N)

        # Mask probabilities by existing network connectivity
        existing_mask = (adj_tensor.sum(dim=-1) > 0.5).float()
        masked_probs = edge_probs * existing_mask

        if not has_batch:
            return masked_probs.squeeze(0)
        return masked_probs
