"""
Multi-Relational Graph Convolutional Network (GCN) for Attack Path Prediction.
Computes spectral-style neighborhood convolutions across 16 Active Directory relation channels.
"""

from typing import Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.data.schema import NUM_EDGE_TYPES, NUM_NODE_FEATURES


class MultiRelationalGCNLayer(nn.Module):
    """
    Graph Convolutional Layer supporting multi-relational adjacency tensors.
    Performs normalized message passing: H^(l+1) = sigma( sum_r D_r^(-1/2) A_r D_r^(-1/2) H^(l) W_r + H^(l) W_self )
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        num_edge_types: int = NUM_EDGE_TYPES,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_edge_types = num_edge_types

        # Per-relation weight transformations
        self.weight_rel = nn.Parameter(torch.Tensor(num_edge_types, in_dim, out_dim))
        self.weight_self = nn.Linear(in_dim, out_dim, bias=True)
        self.norm = nn.LayerNorm(out_dim)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.ReLU()

        self._reset_parameters()

    def _reset_parameters(self):
        nn.init.xavier_uniform_(self.weight_rel)

    def forward(self, x: torch.Tensor, adj_tensor: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, N, in_dim) or (N, in_dim)
            adj_tensor: (B, N, N, num_edge_types) or (N, N, num_edge_types)

        Returns:
            Updated node representations: (B, N, out_dim) or (N, out_dim)
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape
        out_messages = torch.zeros((batch_size, num_nodes, self.out_dim), device=x.device)

        # Message passing across each edge type channel
        for r in range(self.num_edge_types):
            A_r = adj_tensor[:, :, :, r] # (B, N, N)

            # Degree normalization: D^(-1/2) A D^(-1/2)
            deg = A_r.sum(dim=-1) # (B, N)
            deg_inv_sqrt = torch.pow(torch.clamp(deg, min=1e-5), -0.5)
            deg_inv_sqrt[deg == 0] = 0.0
            D_inv_sqrt = torch.diag_embed(deg_inv_sqrt) # (B, N, N)

            A_norm = torch.bmm(torch.bmm(D_inv_sqrt, A_r), D_inv_sqrt) # (B, N, N)

            # H * W_r
            x_w = torch.matmul(x, self.weight_rel[r]) # (B, N, out_dim)
            msg_r = torch.bmm(A_norm, x_w)            # (B, N, out_dim)
            out_messages = out_messages + msg_r

        # Self transformation + residual combination
        self_msg = self.weight_self(x)
        out = out_messages + self_msg
        out = self.norm(out)
        out = self.act(out)
        out = self.dropout(out)

        if not has_batch:
            return out.squeeze(0)
        return out


class GCNModel(nn.Module):
    """
    Multi-Layer GCN with Edge-Pair Likelihood Predictor.
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
        self.name = "GCN_Model"
        self.in_proj = nn.Linear(in_features, hidden_dim)

        self.layers = nn.ModuleList([
            MultiRelationalGCNLayer(
                in_dim=hidden_dim,
                out_dim=hidden_dim,
                num_edge_types=num_edge_types,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])

        self.out_proj = nn.Linear(hidden_dim, out_dim)

        # Edge Pair Classifier MLP: [h_u || h_v || (h_u * h_v) || |h_u - h_v|] -> P(u -> v)
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
            h = h + layer(h, adj_tensor) # Residual skip connection
        h = self.out_proj(h)
        return h

    def forward(self, x: torch.Tensor, adj_tensor: torch.Tensor) -> torch.Tensor:
        """
        Forward pass producing edge attack probability matrix (B, N, N).
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape
        h = self.encode(x, adj_tensor) # (B, N, out_dim)

        # Form pairwise edge representation
        h_u = h.unsqueeze(2).expand(-1, -1, num_nodes, -1) # (B, N, N, D)
        h_v = h.unsqueeze(1).expand(-1, num_nodes, -1, -1) # (B, N, N, D)
        h_mult = h_u * h_v
        h_diff = torch.abs(h_u - h_v)

        edge_feat = torch.cat([h_u, h_v, h_mult, h_diff], dim=-1) # (B, N, N, 4D)
        probs = self.edge_classifier(edge_feat).squeeze(-1)        # (B, N, N)

        # Mask by existing network connectivity
        existing_mask = (adj_tensor.sum(dim=-1) > 0.5).float()
        masked_probs = probs * existing_mask

        if not has_batch:
            return masked_probs.squeeze(0)
        return masked_probs
