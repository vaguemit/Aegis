"""
Multi-Relational GraphSAGE for Attack Path Prediction.
Aggregates inductive local neighborhood features across Active Directory relation channels.
"""

from typing import Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.data.schema import NUM_EDGE_TYPES, NUM_NODE_FEATURES


class MultiRelationalGraphSAGELayer(nn.Module):
    """
    Inductive GraphSAGE layer with per-relation neighborhood aggregation.
    h_v = sigma( W_self * h_v + sum_r W_r * MEAN({h_u : u in N_r(v)}) )
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        num_edge_types: int = NUM_EDGE_TYPES,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_edge_types = num_edge_types

        # Per-relation neighbor transform
        self.rel_linears = nn.ModuleList([
            nn.Linear(in_dim, out_dim, bias=False) for _ in range(num_edge_types)
        ])
        self.self_linear = nn.Linear(in_dim, out_dim, bias=True)
        self.norm = nn.LayerNorm(out_dim)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor, adj_tensor: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, N, in_dim) or (N, in_dim)
            adj_tensor: (B, N, N, num_edge_types) or (N, N, num_edge_types)
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape
        aggregated_neighbors = torch.zeros((batch_size, num_nodes, self.out_dim), device=x.device)

        # Aggregate neighbor embeddings per relation channel
        for r in range(self.num_edge_types):
            A_r = adj_tensor[:, :, :, r] # (B, N, N)

            # Degree row-mean normalization: D^(-1) A
            deg = A_r.sum(dim=-1, keepdim=True) # (B, N, 1)
            deg_inv = torch.reciprocal(torch.clamp(deg, min=1.0))
            deg_inv[deg == 0] = 0.0

            A_mean = A_r * deg_inv # (B, N, N)

            # Aggregate neighbors and project
            neigh_feat = torch.bmm(A_mean, x) # (B, N, in_dim)
            neigh_proj = self.rel_linears[r](neigh_feat) # (B, N, out_dim)
            aggregated_neighbors = aggregated_neighbors + neigh_proj

        self_proj = self.self_linear(x)
        out = aggregated_neighbors + self_proj
        out = self.norm(out)
        out = self.act(out)
        out = self.dropout(out)

        if not has_batch:
            return out.squeeze(0)
        return out


class GraphSAGEModel(nn.Module):
    """
    GraphSAGE Network with Multi-Layer Neighborhood Aggregation & Edge-Pair Predictor.
    """

    def __init__(
        self,
        in_features: int = NUM_NODE_FEATURES,
        hidden_dim: int = 128,
        out_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2,
        num_edge_types: int = NUM_EDGE_TYPES,
    ):
        super().__init__()
        self.name = "GraphSAGE_Model"
        self.in_proj = nn.Linear(in_features, hidden_dim)

        self.layers = nn.ModuleList([
            MultiRelationalGraphSAGELayer(
                in_dim=hidden_dim,
                out_dim=hidden_dim,
                num_edge_types=num_edge_types,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])

        self.out_proj = nn.Linear(hidden_dim, out_dim)

        # Edge Classifier MLP
        self.edge_classifier = nn.Sequential(
            nn.Linear(out_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def encode(self, x: torch.Tensor, adj_tensor: torch.Tensor) -> torch.Tensor:
        """Computes node embeddings H."""
        h = F.relu(self.in_proj(x))
        for layer in self.layers:
            h = h + layer(h, adj_tensor)
        h = self.out_proj(h)
        return h

    def forward(self, x: torch.Tensor, adj_tensor: torch.Tensor) -> torch.Tensor:
        """Forward pass predicting edge attack probability matrix (B, N, N)."""
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape
        h = self.encode(x, adj_tensor)

        h_u = h.unsqueeze(2).expand(-1, -1, num_nodes, -1)
        h_v = h.unsqueeze(1).expand(-1, num_nodes, -1, -1)
        h_mult = h_u * h_v
        h_diff = torch.abs(h_u - h_v)

        edge_feat = torch.cat([h_u, h_v, h_mult, h_diff], dim=-1)
        probs = self.edge_classifier(edge_feat).squeeze(-1)

        existing_mask = (adj_tensor.sum(dim=-1) > 0.5).float()
        masked_probs = probs * existing_mask

        if not has_batch:
            return masked_probs.squeeze(0)
        return masked_probs
