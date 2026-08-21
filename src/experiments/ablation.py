"""
Experiment 2: Feature Ablation Study.
Evaluates the incremental contribution of Enterprise Network Attributes:
Model A: Topology Only
Model B: Topology + OS / Services
Model C: Topology + Vulnerabilities
Model D: Topology + Vulnerabilities + Privileges
Model E: Full Feature Set (All 20 features)
"""

from typing import Dict, List, Any
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from src.data.pignn_loader import PIGNNDataset
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.data.preprocessor import GraphSplitter
from src.models.gat import GATModel
from src.experiments.trainer import ModelTrainer


class AblatedFeatureDataset(Dataset):
    """Dataset wrapper applying active feature masks during ablation."""

    def __init__(self, base_dataset: Any, active_indices: List[int]):
        self.base_dataset = base_dataset
        self.active_indices = active_indices

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int):
        adj_tensor, x_matrix, y_matrix = self.base_dataset[idx]
        x_ablated = torch.zeros_like(x_matrix)
        x_ablated[:, self.active_indices] = x_matrix[:, self.active_indices]
        return adj_tensor, x_ablated, y_matrix


def run_feature_ablation_study(
    num_train_epochs: int = 4,
    max_samples: int = 30,
) -> Dict[str, Dict[str, float]]:
    """Runs the 5-stage feature ablation experiment."""
    print("[*] Starting AegisPath Feature Ablation Experiment...")

    dataset = PIGNNDataset(data_dir="data/_data_", max_samples=max_samples)
    if len(dataset) < 10:
        gen = SyntheticEnterpriseGenerator(seed=42)
        dataset = [gen.generate() for _ in range(max_samples)]

    splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    train_raw, _, test_raw = splitter.split(dataset)

    # Define Feature Subsets (Indices in 0..19)
    # Entity Types: 0..5
    # Security Props: 6..11 (enabled, hasspn, highvalue, is_vulnerable, target, owned)
    # OS: 12..19
    feature_configurations = {
        "A: Topology Only": list(range(0, 6)),
        "B: Topology + OS": list(range(0, 6)) + list(range(12, 20)),
        "C: Topology + Vulnerabilities": list(range(0, 6)) + [9], # 9 is is_vulnerable
        "D: Topology + Vulns + Privileges": list(range(0, 6)) + [7, 8, 9], # hasspn, highvalue, is_vulnerable
        "E: Full Feature Set": list(range(0, 20)),
    }

    ablation_results = {}
    baseline_f1 = 0.0

    for config_name, active_cols in feature_configurations.items():
        print(f"[+] Training GAT on Feature Configuration '{config_name}' ({len(active_cols)} active features)...")
        train_ds = AblatedFeatureDataset(train_raw, active_cols)
        test_ds = AblatedFeatureDataset(test_raw, active_cols)

        train_loader = DataLoader(train_ds, batch_size=8, shuffle=True)
        test_loader = DataLoader(test_ds, batch_size=8, shuffle=False)

        model = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
        trainer = ModelTrainer(model, learning_rate=1e-3)

        for _ in range(num_train_epochs):
            trainer.train_epoch(train_loader)

        metrics = trainer.evaluate(test_loader)
        if config_name == "A: Topology Only":
            baseline_f1 = metrics.f1

        delta_f1 = metrics.f1 - baseline_f1
        ablation_results[config_name] = {
            "active_features": len(active_cols),
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "roc_auc": metrics.roc_auc,
            "pr_auc": metrics.pr_auc,
            "delta_f1_gain": delta_f1,
        }

    print("\n" + "=" * 80)
    print("                    AEGISPATH FEATURE ABLATION RESULTS")
    print("=" * 80)
    print(f"{'Feature Configuration':<36} | {'Features':<8} | {'F1-Score':<8} | {'ROC-AUC':<8} | {'ΔF1 Gain':<8}")
    print("-" * 80)
    for config_name, res in ablation_results.items():
        print(
            f"{config_name:<36} | "
            f"{res['active_features']:>8d} | "
            f"{res['f1']:>8.4f} | "
            f"{res['roc_auc']:>8.4f} | "
            f"{res['delta_f1_gain']:>+8.4f}"
        )
    print("=" * 80)

    return ablation_results


if __name__ == "__main__":
    run_feature_ablation_study(num_train_epochs=3, max_samples=25)
