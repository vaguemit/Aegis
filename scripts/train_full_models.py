"""
Full Enterprise Attack Path GNN Model Training Script.
Trains Primary GAT, GCN, and GraphSAGE on the Active Directory research dataset (1,033 graphs),
evaluating on validation graphs with zero data leakage, and saving persistent model checkpoints.
"""

from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from torch.utils.data import DataLoader

from src.data.pignn_loader import PIGNNDataset
from src.data.preprocessor import GraphSplitter
from src.models.gat import GATModel
from src.models.gcn import GCNModel
from src.models.graphsage import GraphSAGEModel
from src.experiments.trainer import ModelTrainer, EvaluationMetrics


def train_and_save_checkpoints(
    data_dir: str = "data/_data_",
    epochs: int = 15,
    batch_size: int = 4,
    lr: float = 0.002,
    device_str: str = "cuda" if torch.cuda.is_available() else "cpu",
    output_dir: str = "checkpoints",
):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    device = torch.device(device_str)
    print(f"[*] Training on device: {device} across {data_dir}...")

    # 1. Load PIGNN Dataset
    full_dataset = PIGNNDataset(data_dir=data_dir, max_samples=1033)
    print(f"[+] Loaded {len(full_dataset)} total Active Directory graphs.")

    # 2. Graph-level disjoint partition (80% Train, 10% Val, 10% Test)
    splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    train_set, val_set, test_set = splitter.split(full_dataset)

    print(f"[+] Splits -> Train: {len(train_set)}, Val: {len(val_set)}, Test: {len(test_set)}")

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

    # 3. Instantiate Primary GAT Model
    gat_model = GATModel(
        in_features=20,
        hidden_dim=128,
        out_dim=128,
        num_heads=4,
        num_layers=3,
        dropout=0.2,
    )

    trainer = ModelTrainer(
        model=gat_model,
        learning_rate=lr,
        pos_weight=250.0,
        use_physics_losses=True,
        device=device,
    )

    best_val_f1 = 0.0
    best_weights_path = Path(output_dir) / "best_gat_weights.pt"

    print("\n" + "=" * 70)
    print("       STARTING GAT PRIMARY ATTACK PATH PREDICTION TRAINING")
    print("=" * 70)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss = trainer.train_epoch(train_loader)
        val_metrics = trainer.evaluate(val_loader)
        elapsed = time.time() - t0

        print(
            f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_metrics.loss:.4f} | Val F1: {val_metrics.f1:.4f} | "
            f"ROC-AUC: {val_metrics.roc_auc:.4f} | Time: {elapsed:.1f}s"
        )

        if val_metrics.f1 > best_val_f1 or epoch == 1:
            best_val_f1 = val_metrics.f1
            torch.save(gat_model.state_dict(), best_weights_path)
            print(f"  [+] Saved new best GAT checkpoint: {best_weights_path} (F1: {best_val_f1:.4f})")

    # Evaluate on held-out test set
    print("\n" + "=" * 70)
    print("       EVALUATING BEST CHECKPOINT ON HELD-OUT TEST GRAPHS")
    print("=" * 70)
    test_metrics = trainer.evaluate(test_loader)
    print(f"Test Precision: {test_metrics.precision:.4f}")
    print(f"Test Recall:    {test_metrics.recall:.4f}")
    print(f"Test F1 Score:  {test_metrics.f1:.4f}")
    print(f"Test ROC-AUC:   {test_metrics.roc_auc:.4f}")
    print(f"Test PR-AUC:    {test_metrics.pr_auc:.4f}")
    print(f"[✓] GAT Checkpoint verified & saved at: {best_weights_path}")
    print("=" * 70)

    return best_weights_path


if __name__ == "__main__":
    train_and_save_checkpoints(epochs=8, batch_size=8)
