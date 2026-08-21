"""Generate benchmark and ablation research charts."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.experiments.plotter import (
    plot_benchmark_comparison,
    plot_feature_ablation,
    plot_scalability_curves,
)
from backend.routes.experiments import get_benchmark_results, get_ablation_results
from src.experiments.scalability import run_scalability_benchmark

if __name__ == "__main__":
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    print("[*] Generating benchmark figures...")
    plot_benchmark_comparison(get_benchmark_results(), "artifacts/benchmark_comparison.png")
    plot_feature_ablation(get_ablation_results(), "artifacts/feature_ablation.png")
    scale_res = run_scalability_benchmark(node_scales=[20, 50, 100, 200])
    plot_scalability_curves(scale_res, "artifacts/scalability_curves.png")
    print("[+] All research figures generated successfully in artifacts/")
