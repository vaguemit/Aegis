"""
Model Trainer and Evaluator for AegisPath GNN Architectures.
Includes training loops, early stopping, learning rate schedulers,
and standard classification metrics (Precision, Recall, F1, ROC-AUC, PR-AUC).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

from src.models.losses import FocalEdgeLoss, WeightedMaskedBCELoss, DegreePenaltyLoss, CycleSuppressionLoss


@dataclass
class EvaluationMetrics:
    """Evaluation metrics summary across graph edge predictions."""
    loss: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    path_accuracy: float
    avg_inference_time_ms: float


class ModelTrainer:
    """
    Standardized trainer for GCN, GraphSAGE, and GAT models on enterprise graphs.
    """

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        pos_weight: float = 250.0,
        use_physics_losses: bool = True,
        device: Optional[torch.device] = None,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )
        self.scheduler = torch.optim.lr_scheduler.ExponentialLR(self.optimizer, gamma=0.98)

        self.bce_loss_fn = WeightedMaskedBCELoss(pos_weight=pos_weight)
        self.focal_loss_fn = FocalEdgeLoss(alpha=0.85, gamma=2.0)
        self.deg_loss_fn = DegreePenaltyLoss(weight=0.05)
        self.cycle_loss_fn = CycleSuppressionLoss(max_k=4, weight=0.02)
        self.use_physics_losses = use_physics_losses

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Trains for one epoch across the dataloader."""
        self.model.train()
        total_loss = 0.0
        batch_count = 0

        for adj_tensor, x_matrix, y_matrix in dataloader:
            adj_tensor = adj_tensor.to(self.device)
            x_matrix = x_matrix.to(self.device)
            y_matrix = y_matrix.to(self.device)

            self.optimizer.zero_grad()

            pred_probs = self.model(x_matrix, adj_tensor)

            # Combined loss calculation
            existing_mask = (adj_tensor.sum(dim=-1) > 0.5).float()
            loss = self.bce_loss_fn(pred_probs, y_matrix, existing_edges_mask=existing_mask)

            if self.use_physics_losses:
                deg_l = self.deg_loss_fn(pred_probs)
                cyc_l = self.cycle_loss_fn(pred_probs)
                loss = loss + deg_l + cyc_l

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=2.0)
            self.optimizer.step()

            total_loss += float(loss.item())
            batch_count += 1

        self.scheduler.step()
        return total_loss / max(1, batch_count)

    def evaluate(
        self,
        dataloader: DataLoader,
        threshold: float = 0.5,
    ) -> EvaluationMetrics:
        """Evaluates model performance on validation or test dataset."""
        self.model.eval()
        all_preds = []
        all_targets = []
        total_loss = 0.0
        batch_count = 0
        timing_list = []

        with torch.no_grad():
            for adj_tensor, x_matrix, y_matrix in dataloader:
                adj_tensor = adj_tensor.to(self.device)
                x_matrix = x_matrix.to(self.device)
                y_matrix = y_matrix.to(self.device)

                t0 = time.perf_counter()
                pred_probs = self.model(x_matrix, adj_tensor)
                t1 = time.perf_counter()
                timing_list.append((t1 - t0) * 1000.0)

                loss = self.bce_loss_fn(pred_probs, y_matrix)
                total_loss += float(loss.item())
                batch_count += 1

                # Restrict metrics to actual topologically existing edges in the network
                existing_mask = (adj_tensor.sum(dim=-1) > 0.5)
                valid_preds = pred_probs[existing_mask].cpu().numpy()
                valid_targets = y_matrix[existing_mask].cpu().numpy()

                all_preds.extend(valid_preds.tolist())
                all_targets.extend(valid_targets.tolist())

        y_true = np.array(all_targets, dtype=np.int32)
        y_prob = np.array(all_preds, dtype=np.float32)
        y_pred = (y_prob >= threshold).astype(np.int32)

        # Compute classification metrics
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y_true, y_prob))
        except Exception:
            pr_auc = float(np.mean(y_true))

        # Path accuracy metric (if top predicted edges match ground truth)
        top_k_indices = np.argsort(y_prob)[-int(np.sum(y_true)):] if np.sum(y_true) > 0 else []
        top_k_hits = np.sum(y_true[top_k_indices]) if len(top_k_indices) > 0 else 0
        path_acc = float(top_k_hits / max(1.0, float(np.sum(y_true))))

        return EvaluationMetrics(
            loss=total_loss / max(1, batch_count),
            precision=precision,
            recall=recall,
            f1=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            path_accuracy=path_acc,
            avg_inference_time_ms=float(np.mean(timing_list)) if timing_list else 0.0,
        )
