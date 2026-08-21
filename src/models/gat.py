"""
Graph Attention Network (GAT) for Attack Path Prediction (Primary Model).
Implements multi-head relational graph attention with edge-type conditioning,
attention weight caching for explainability, and pairwise lateral movement link prediction.
"""

from typing import Optional, List, Tuple, Dict, Any
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.data.schema import NUM_EDGE_TYPES, NUM_NODE_FEATURES


class MultiHeadRelationalGATLayer(nn.Module):
    """
    Multi-Head Graph Attention Layer with Relational Edge Conditioning.
    Computes masked attention coefficients alpha_ij between connected nodes:
    alpha_ij = softmax_j( LeakyReLU( a_src^T W h_i + a_dst^T W h_j + r_type_bias ) )
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        num_heads: int = 4,
        num_edge_types: int = NUM_EDGE_TYPES,
        concat_heads: bool = True,
        dropout: float = 0.2,
        leaky_relu_slope: float = 0.2,
    ):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_heads = num_heads
        self.num_edge_types = num_edge_types
        self.concat_heads = concat_heads
        self.dropout = nn.Dropout(dropout)
        self.leaky_relu = nn.LeakyReLU(leaky_relu_slope)

        # Head projection dimensions
        if concat_heads:
            assert out_dim % num_heads == 0, "out_dim must be divisible by num_heads when concat_heads=True"
            self.head_dim = out_dim // num_heads
        else:
            self.head_dim = out_dim

        # Linear transformations for all heads
        self.w_proj = nn.Linear(in_dim, self.num_heads * self.head_dim, bias=False)

        # Source and destination attention parameter vectors
        self.attn_src = nn.Parameter(torch.Tensor(1, num_heads, 1, self.head_dim))
        self.attn_dst = nn.Parameter(torch.Tensor(1, num_heads, 1, self.head_dim))

        # Relational edge type bias embeddings: (num_edge_types, num_heads, 1, 1)
        self.rel_bias = nn.Parameter(torch.Tensor(num_edge_types, num_heads))

        self.norm = nn.LayerNorm(out_dim)
        self._last_attention_weights: Optional[torch.Tensor] = None # Cached for XAI

        self._reset_parameters()

    def _reset_parameters(self):
        nn.init.xavier_uniform_(self.w_proj.weight)
        nn.init.xavier_uniform_(self.attn_src)
        nn.init.xavier_uniform_(self.attn_dst)
        nn.init.zeros_(self.rel_bias)

    def forward(
        self,
        x: torch.Tensor,
        adj_tensor: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor:
        """
        Args:
            x: Node features of shape (B, N, in_dim) or (N, in_dim)
            adj_tensor: Adjacency tensor of shape (B, N, N, num_edge_types) or (N, N, num_edge_types)
            return_attention: If True, saves attention weights for explainability

        Returns:
            Updated node representations of shape (B, N, out_dim) or (N, out_dim)
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape

        # 1. Project node features for all heads: (B, N, num_heads * head_dim) -> (B, num_heads, N, head_dim)
        h = self.w_proj(x)
        h = h.view(batch_size, num_nodes, self.num_heads, self.head_dim).permute(0, 2, 1, 3)

        # 2. Compute self attention components
        # (B, num_heads, N, 1)
        score_src = (h * self.attn_src).sum(dim=-1, keepdim=True)
        score_dst = (h * self.attn_dst).sum(dim=-1, keepdim=True)

        # Broadcasted pairwise score: e_ij = score_src_i + score_dst_j -> (B, num_heads, N, N)
        scores = score_src + score_dst.permute(0, 1, 3, 2)

        # 3. Add relational edge biases
        # Combine multi-relation channels into total adjacency and add relation bias
        # adj_tensor: (B, N, N, R) -> (B, R, N, N)
        adj_perm = adj_tensor.permute(0, 3, 1, 2)
        total_adj = (adj_perm.sum(dim=1) > 0.5) # (B, N, N) boolean mask of existing edges

        # Compute relational bias contribution
        # rel_bias: (R, H) -> (1, H, R, 1, 1)
        rel_bias_exp = self.rel_bias.t().unsqueeze(0).unsqueeze(-1).unsqueeze(-1) # (1, H, R, 1, 1)
        adj_exp = adj_perm.unsqueeze(1) # (B, 1, R, N, N)
        rel_contrib = (adj_exp * rel_bias_exp).sum(dim=2) # (B, H, N, N)

        scores = self.leaky_relu(scores + rel_contrib)

        # 4. Mask scores where no physical edge exists in the network
        mask = total_adj.unsqueeze(1).expand(-1, self.num_heads, -1, -1) # (B, H, N, N)
        scores = scores.masked_fill(~mask, -1e9)

        # Softmax over neighbors (dim=-1)
        attn_weights = F.softmax(scores, dim=-1)
        # Handle isolated nodes with no incoming edges (softmax of all -inf becomes nan)
        attn_weights = torch.nan_to_num(attn_weights, nan=0.0)
        attn_weights_drop = self.dropout(attn_weights)

        if return_attention:
            self._last_attention_weights = attn_weights.detach()

        # 5. Aggregate neighbor features: (B, H, N, N) x (B, H, N, D_h) -> (B, H, N, D_h)
        out = torch.matmul(attn_weights_drop, h)

        # 6. Combine heads
        if self.concat_heads:
            # (B, H, N, D_h) -> (B, N, H * D_h)
            out = out.permute(0, 2, 1, 3).contiguous().view(batch_size, num_nodes, self.num_heads * self.head_dim)
        else:
            # Mean across heads: (B, N, D_h)
            out = out.mean(dim=1)

        out = self.norm(out)

        if not has_batch:
            return out.squeeze(0)
        return out


class GATModel(nn.Module):
    """
    Primary Architecture: Multi-Head Graph Attention Network with Edge-Pair Attack Predictor.
    """

    def __init__(
        self,
        in_features: int = NUM_NODE_FEATURES,
        hidden_dim: int = 128,
        out_dim: int = 128,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.2,
        num_edge_types: int = NUM_EDGE_TYPES,
    ):
        super().__init__()
        self.name = "GAT_Primary_Model"
        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.num_heads = num_heads

        # Input feature projection
        self.in_proj = nn.Linear(in_features, hidden_dim)

        # Stack of GAT Layers
        self.layers = nn.ModuleList([
            MultiHeadRelationalGATLayer(
                in_dim=hidden_dim,
                out_dim=hidden_dim,
                num_heads=num_heads,
                num_edge_types=num_edge_types,
                concat_heads=True,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])

        self.out_proj = nn.Linear(hidden_dim, out_dim)

        # Edge-Pair Attack Probability MLP:
        # Input: [h_u || h_v || (h_u * h_v) || |h_u - h_v|] (dimension: 4 * out_dim)
        self.edge_classifier = nn.Sequential(
            nn.Linear(out_dim * 4, hidden_dim),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LeakyReLU(0.2),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def encode(
        self,
        x: torch.Tensor,
        adj_tensor: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor:
        """Computes contextualized node embeddings using relational multi-head attention."""
        h = F.relu(self.in_proj(x))
        for layer in self.layers:
            h = h + layer(h, adj_tensor, return_attention=return_attention) # Residual connection
        h = self.out_proj(h)
        return h

    def forward(
        self,
        x: torch.Tensor,
        adj_tensor: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor:
        """
        Forward pass predicting edge attack likelihood P(u -> v) for all node pairs.

        Args:
            x: (B, N, F) or (N, F)
            adj_tensor: (B, N, N, R) or (N, N, R)

        Returns:
            Probability matrix of shape (B, N, N) or (N, N) with values in [0, 1].
        """
        has_batch = (x.dim() == 3)
        if not has_batch:
            x = x.unsqueeze(0)
            adj_tensor = adj_tensor.unsqueeze(0)

        batch_size, num_nodes, _ = x.shape
        h = self.encode(x, adj_tensor, return_attention=return_attention) # (B, N, out_dim)

        # Pairwise representations
        h_u = h.unsqueeze(2).expand(-1, -1, num_nodes, -1)
        h_v = h.unsqueeze(1).expand(-1, num_nodes, -1, -1)
        h_mult = h_u * h_v
        h_diff = torch.abs(h_u - h_v)

        edge_feat = torch.cat([h_u, h_v, h_mult, h_diff], dim=-1) # (B, N, N, 4D)
        probs = self.edge_classifier(edge_feat).squeeze(-1)        # (B, N, N)

        # Enforce that only topologically existing network connections can be predicted
        existing_mask = (adj_tensor.sum(dim=-1) > 0.5).float()
        masked_probs = probs * existing_mask

        if not has_batch:
            return masked_probs.squeeze(0)
        return masked_probs

    def get_attention_weights(self) -> List[torch.Tensor]:
        """Returns cached attention weights from all GAT layers for XAI visualization."""
        weights = []
        for layer in self.layers:
            if hasattr(layer, "_last_attention_weights") and layer._last_attention_weights is not None:
                weights.append(layer._last_attention_weights)
        return weights
