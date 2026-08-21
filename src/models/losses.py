"""
Custom Loss Functions for Graph Attack Path and Edge Prediction.
Includes Focal Edge Loss, Weighted Masked BCE, Degree Regularization,
and Cycle Suppression Loss.
"""

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalEdgeLoss(nn.Module):
    """
    Focal Loss adapted for extreme graph edge class imbalance.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, alpha: float = 0.85, gamma: float = 2.0, reduction: str = "mean"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, pred_probs: torch.Tensor, target_labels: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred_probs: Predicted probabilities in range [0, 1], shape (...)
            target_labels: Ground truth binary labels in {0, 1}, shape (...)
        """
        eps = 1e-7
        p = torch.clamp(pred_probs, eps, 1.0 - eps)
        target = target_labels.float()

        # Binary focal loss formulation
        p_t = p * target + (1.0 - p) * (1.0 - target)
        alpha_t = self.alpha * target + (1.0 - self.alpha) * (1.0 - target)
        focal_weight = alpha_t * torch.pow(1.0 - p_t, self.gamma)
        loss = -focal_weight * torch.log(p_t)

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class WeightedMaskedBCELoss(nn.Module):
    """
    Masked Binary Cross-Entropy with Positive Class Weighting.
    Includes all positive attack-path edges and subsamples negative edges
    to prevent the model from collapsing to trivial all-zero predictions.
    """

    def __init__(
        self,
        pos_weight: float = 300.0,
        neg_sample_rate: float = 0.005,
        eps: float = 1e-7,
    ):
        super().__init__()
        self.pos_weight = pos_weight
        self.neg_sample_rate = neg_sample_rate
        self.eps = eps

    def forward(
        self,
        pred_probs: torch.Tensor,
        target_labels: torch.Tensor,
        existing_edges_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            pred_probs: Predicted probabilities (B, N, N) or (N, N)
            target_labels: Ground truth binary matrix (B, N, N) or (N, N)
            existing_edges_mask: Optional mask of actual network edges (B, N, N)
        """
        target = target_labels.float()
        p = torch.clamp(pred_probs, self.eps, 1.0 - self.eps)

        # Build training mask: all positive edges + sampled negative edges
        rand_mask = torch.rand_like(target) < self.neg_sample_rate
        if existing_edges_mask is not None:
            # Prioritize negative sampling on actual existing network edges
            rand_mask = rand_mask | (existing_edges_mask.bool() & (target == 0))

        active_mask = (target > 0.5) | rand_mask

        # Weight positive vs negative elements
        weights = torch.ones_like(target)
        weights[target > 0.5] = self.pos_weight

        bce = -(
            weights * target * torch.log(p)
            + (1.0 - target) * torch.log(1.0 - p)
        )

        masked_loss = bce * active_mask.float()
        num_active = torch.clamp(active_mask.float().sum(), min=1.0)
        return masked_loss.sum() / num_active


class DegreePenaltyLoss(nn.Module):
    """
    Penalizes multi-branching to encourage clean linear attack paths.
    Enforces in_degree=1, out_degree=1 on intermediate attack path nodes.
    """

    def __init__(self, weight: float = 0.1):
        super().__init__()
        self.weight = weight

    def forward(self, pred_adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred_adj: Predicted adjacency matrix (B, N, N) or (N, N)
        """
        if pred_adj.dim() == 2:
            pred_adj = pred_adj.unsqueeze(0)

        deg_out = pred_adj.sum(dim=-1) # (B, N)
        deg_in = pred_adj.sum(dim=-2)  # (B, N)

        active = (deg_in > 0.1) | (deg_out > 0.1)
        start_nodes = (deg_in < 0.1) & (deg_out > 0.1)
        end_nodes = (deg_out < 0.1) & (deg_in > 0.1)

        p_start = (start_nodes.float().sum(dim=-1) - 1.0).pow(2)
        p_end = (end_nodes.float().sum(dim=-1) - 1.0).pow(2)

        # Intermediate nodes must have deg_in ~ 1 and deg_out ~ 1
        intermediate = active & (~start_nodes) & (~end_nodes)
        p_inter = (
            (deg_in - 1.0).pow(2) * intermediate.float()
            + (deg_out - 1.0).pow(2) * intermediate.float()
        ).sum(dim=-1)

        loss = (p_start + p_end + p_inter).mean()
        return self.weight * loss


class CycleSuppressionLoss(nn.Module):
    """
    Penalizes cyclic attack trajectories using powers of the transition matrix:
    L_cycle = sum_{k=1}^K (1/k) * Tr(P^k)
    """

    def __init__(self, max_k: int = 5, weight: float = 0.05, eps: float = 1e-6):
        super().__init__()
        self.max_k = max_k
        self.weight = weight
        self.eps = eps

    def forward(self, pred_adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pred_adj: Shape (B, N, N) or (N, N)
        """
        if pred_adj.dim() == 2:
            pred_adj = pred_adj.unsqueeze(0)

        batch_size, num_nodes, _ = pred_adj.shape
        # Normalize row-stochastically
        row_sum = pred_adj.sum(dim=-1, keepdim=True) + self.eps
        trans_prob = pred_adj / row_sum

        cycle_penalty = torch.zeros(batch_size, device=pred_adj.device)
        power_mat = torch.eye(num_nodes, device=pred_adj.device).unsqueeze(0).expand(batch_size, -1, -1)

        for k in range(1, self.max_k + 1):
            power_mat = torch.bmm(power_mat, trans_prob)
            # Trace of power_mat is sum of diagonal elements (paths returning to self in k hops)
            diag_sum = torch.diagonal(power_mat, dim1=-2, dim2=-1).sum(dim=-1)
            cycle_penalty += diag_sum / float(k)

        return self.weight * cycle_penalty.mean()
