"""
Research Plotting and Visualization Generator.
Produces high-resolution figures for academic reports and presentations:
- Model Benchmark Comparison
- Feature Ablation Impact
- Scalability Latency vs Network Size
- GAT Multi-Head Attention Heatmaps
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import numpy as np


def plot_benchmark_comparison(
    benchmark_results: Dict[str, Dict[str, float]],
    output_path: str = "artifacts/benchmark_comparison.png",
):
    """Plots comparative bar charts across models for F1, ROC-AUC, and Precision/Recall."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    models = list(benchmark_results.keys())
    f1_scores = [benchmark_results[m]["f1"] for m in models]
    roc_scores = [benchmark_results[m]["roc_auc"] for m in models]
    pr_scores = [benchmark_results[m]["pr_auc"] for m in models]

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    rects1 = ax.bar(x - width, f1_scores, width, label="F1-Score", color="#2563eb")
    rects2 = ax.bar(x, roc_scores, width, label="ROC-AUC", color="#10b981")
    rects3 = ax.bar(x + width, pr_scores, width, label="PR-AUC", color="#f59e0b")

    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title("AegisPath: Classical Baselines vs. GNN Model Benchmark", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right", fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Saved benchmark figure to {output_path}")


def plot_feature_ablation(
    ablation_results: Dict[str, Dict[str, float]],
    output_path: str = "artifacts/feature_ablation.png",
):
    """Plots feature ablation progression showing contribution of attributes to F1 and ROC-AUC."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    configs = list(ablation_results.keys())
    f1_scores = [ablation_results[c]["f1"] for c in configs]
    roc_scores = [ablation_results[c]["roc_auc"] for c in configs]

    x = np.arange(len(configs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    ax.bar(x - width/2, f1_scores, width, label="F1-Score", color="#3b82f6")
    ax.bar(x + width/2, roc_scores, width, label="ROC-AUC", color="#8b5cf6")

    ax.set_ylabel("Metric Score", fontsize=12, fontweight="bold")
    ax.set_title("AegisPath: Feature Ablation Study (Enterprise Attributes Contribution)", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(configs, rotation=15, ha="right", fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Saved ablation figure to {output_path}")


def plot_scalability_curves(
    scalability_results: List[Dict[str, Any]],
    output_path: str = "artifacts/scalability_curves.png",
):
    """Plots latency and memory scaling as network size grows to 1,000 nodes."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    nodes = [r["actual_nodes"] for r in scalability_results]
    gat_lat = [r["gat_inference_ms"] for r in scalability_results]
    bs_lat = [r["beam_search_ms"] for r in scalability_results]
    total_lat = [r["total_latency_ms"] for r in scalability_results]
    mem_mb = [r["approx_mem_mb"] for r in scalability_results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    # Latency Plot
    ax1.plot(nodes, total_lat, marker="o", linewidth=2, color="#ef4444", label="Total Latency (ms)")
    ax1.plot(nodes, gat_lat, marker="s", linewidth=1.5, linestyle="--", color="#3b82f6", label="GAT Inference (ms)")
    ax1.plot(nodes, bs_lat, marker="^", linewidth=1.5, linestyle=":", color="#10b981", label="Beam Search (ms)")
    ax1.set_xlabel("Network Node Count (|V|)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Latency (milliseconds)", fontsize=11, fontweight="bold")
    ax1.set_title("Inference & Path Search Latency", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    # Memory Plot
    ax2.plot(nodes, mem_mb, marker="D", linewidth=2, color="#8b5cf6", label="Graph Tensor Memory (MB)")
    ax2.set_xlabel("Network Node Count (|V|)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Memory (MB)", fontsize=11, fontweight="bold")
    ax2.set_title("Memory Consumption Scaling", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Saved scalability figure to {output_path}")
