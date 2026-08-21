"""
Experiment 1: Comprehensive Model Benchmark.
Compares Classical Baselines, Embedding Models, and Graph Neural Networks (GCN, GraphSAGE, GAT).
Evaluates Precision, Recall, F1-Score, ROC-AUC, PR-AUC, and Path Accuracy.
"""

from typing import Dict, List, Any
import json
import time
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

from src.data.pignn_loader import PIGNNDataset
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.data.preprocessor import GraphSplitter
from src.models.baselines import (
    DijkstraShortestPathBaseline,
    CVSSWeightedShortestPathBaseline,
    BiasedRandomWalkBaseline,
    Node2VecBaseline,
)
from src.models.gcn import GCNModel
from src.models.graphsage import GraphSAGEModel
from src.models.gat import GATModel
from src.experiments.trainer import ModelTrainer, EvaluationMetrics


def evaluate_classical_baseline(
    baseline_obj: Any,
    test_graphs: List[Any],
    baseline_type: str = "dijkstra",
) -> Dict[str, float]:
    """Evaluates a non-neural baseline across a list of test graphs."""
    all_preds = []
    all_targets = []
    timings = []

    for g in test_graphs:
        adj = g.adj_tensor
        x = g.x_matrix
        y = g.y_matrix
        src = g.source_idx
        dst = g.target_idx

        t0 = time.perf_counter()
        if baseline_type == "dijkstra":
            prob_mat = baseline_obj.predict_edge_probs(adj, src, dst)
        elif baseline_type == "cvss":
            prob_mat = baseline_obj.predict_edge_probs(adj, x, src, dst)
        elif baseline_type == "random_walk":
            prob_mat = baseline_obj.predict_edge_probs(adj, x, src, dst)
        else:
            prob_mat = baseline_obj.predict_edge_probs(adj, src, dst)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)

        existing_mask = (adj.sum(dim=-1) > 0.5)
        valid_preds = prob_mat[existing_mask].cpu().numpy()
        valid_targets = y[existing_mask].cpu().numpy()

        all_preds.extend(valid_preds.tolist())
        all_targets.extend(valid_targets.tolist())

    y_true = np.array(all_targets, dtype=np.int32)
    y_prob = np.array(all_preds, dtype=np.float32)
    y_pred = (y_prob >= 0.5).astype(np.int32)

    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        roc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc = 0.5
    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except Exception:
        pr_auc = float(np.mean(y_true))

    return {
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc,
        "pr_auc": pr_auc,
        "latency_ms": float(np.mean(timings)) if timings else 0.0,
    }


def run_full_benchmark(
    num_train_epochs: int = 5,
    max_samples: int = 40,
) -> Dict[str, Any]:
    """
    Executes benchmark comparison across all 7 models.
    """
    print(f"[*] Starting AegisPath Model Benchmark (max_samples={max_samples}, epochs={num_train_epochs})...")

    # Load benchmark dataset or synthesize if needed
    dataset = PIGNNDataset(data_dir="data/_data_", max_samples=max_samples)
    if len(dataset) < 10:
        print("[!] Generating synthetic dataset for benchmarking...")
        gen = SyntheticEnterpriseGenerator(seed=42)
        dataset = [gen.generate() for _ in range(max_samples)]

    splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    train_set, val_set, test_set = splitter.split(dataset)

    train_loader = DataLoader(train_set, batch_size=8, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=8, shuffle=False)

    # Convert test set to graph objects for classical baselines
    test_graphs = [dataset[i] if isinstance(dataset, list) else dataset.get_graph(i) for i in test_set.indices]

    results: Dict[str, Dict[str, float]] = {}

    # 1. Dijkstra Baseline
    print("[+] Evaluating Baseline 1: Dijkstra Shortest Path...")
    dijkstra = DijkstraShortestPathBaseline()
    results["Dijkstra Shortest Path"] = evaluate_classical_baseline(dijkstra, test_graphs, "dijkstra")

    # 2. CVSS-Weighted Baseline
    print("[+] Evaluating Baseline 2: CVSS-Weighted Shortest Path...")
    cvss = CVSSWeightedShortestPathBaseline()
    results["CVSS-Weighted Walk"] = evaluate_classical_baseline(cvss, test_graphs, "cvss")

    # 3. Biased Random Walk
    print("[+] Evaluating Baseline 3: Biased Random Walk...")
    rw = BiasedRandomWalkBaseline(num_walks=30, max_steps=15)
    results["Biased Random Walk"] = evaluate_classical_baseline(rw, test_graphs, "random_walk")

    # 4. Node2Vec + Classifier
    print("[+] Evaluating Baseline 4: Node2Vec Embeddings...")
    sample_g = test_graphs[0]
    num_nodes = sample_g.num_nodes if hasattr(sample_g, "num_nodes") else sample_g[1].shape[0]
    node2vec = Node2VecBaseline(num_nodes=num_nodes, in_features=20, embedding_dim=32)
    trainer_n2v = ModelTrainer(node2vec, learning_rate=2e-3)
    for _ in range(num_train_epochs):
        trainer_n2v.train_epoch(train_loader)
    eval_n2v = trainer_n2v.evaluate(test_loader)
    results["Node2Vec Classifier"] = {
        "precision": eval_n2v.precision,
        "recall": eval_n2v.recall,
        "f1": eval_n2v.f1,
        "roc_auc": eval_n2v.roc_auc,
        "pr_auc": eval_n2v.pr_auc,
        "latency_ms": eval_n2v.avg_inference_time_ms,
    }

    # 5. GCN Model
    print("[+] Evaluating Model 5: Graph Convolutional Network (GCN)...")
    gcn = GCNModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
    trainer_gcn = ModelTrainer(gcn, learning_rate=1e-3)
    for _ in range(num_train_epochs):
        trainer_gcn.train_epoch(train_loader)
    eval_gcn = trainer_gcn.evaluate(test_loader)
    results["GCN"] = {
        "precision": eval_gcn.precision,
        "recall": eval_gcn.recall,
        "f1": eval_gcn.f1,
        "roc_auc": eval_gcn.roc_auc,
        "pr_auc": eval_gcn.pr_auc,
        "latency_ms": eval_gcn.avg_inference_time_ms,
    }

    # 6. GraphSAGE Model
    print("[+] Evaluating Model 6: GraphSAGE...")
    sage = GraphSAGEModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
    trainer_sage = ModelTrainer(sage, learning_rate=1e-3)
    for _ in range(num_train_epochs):
        trainer_sage.train_epoch(train_loader)
    eval_sage = trainer_sage.evaluate(test_loader)
    results["GraphSAGE"] = {
        "precision": eval_sage.precision,
        "recall": eval_sage.recall,
        "f1": eval_sage.f1,
        "roc_auc": eval_sage.roc_auc,
        "pr_auc": eval_sage.pr_auc,
        "latency_ms": eval_sage.avg_inference_time_ms,
    }

    # 7. GAT Primary Model
    print("[+] Evaluating Model 7: Graph Attention Network (GAT - Primary)...")
    gat = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
    trainer_gat = ModelTrainer(gat, learning_rate=1e-3)
    for _ in range(num_train_epochs):
        trainer_gat.train_epoch(train_loader)
    eval_gat = trainer_gat.evaluate(test_loader)
    results["GAT (Primary)"] = {
        "precision": eval_gat.precision,
        "recall": eval_gat.recall,
        "f1": eval_gat.f1,
        "roc_auc": eval_gat.roc_auc,
        "pr_auc": eval_gat.pr_auc,
        "latency_ms": eval_gat.avg_inference_time_ms,
    }

    print("\n" + "=" * 80)
    print("                      AEGISPATH MODEL BENCHMARK RESULTS")
    print("=" * 80)
    print(f"{'Model':<28} | {'Precision':<10} | {'Recall':<8} | {'F1-Score':<8} | {'ROC-AUC':<8} | {'PR-AUC':<8} | {'Latency':<8}")
    print("-" * 80)
    for model_name, metrics in results.items():
        print(
            f"{model_name:<28} | "
            f"{metrics['precision']*100:>8.2f}% | "
            f"{metrics['recall']*100:>6.2f}% | "
            f"{metrics['f1']:>8.4f} | "
            f"{metrics['roc_auc']:>8.4f} | "
            f"{metrics['pr_auc']:>8.4f} | "
            f"{metrics['latency_ms']:>6.1f}ms"
        )
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_full_benchmark(num_train_epochs=3, max_samples=30)
