"""Research experiments, benchmarks, feature ablation, scalability, and plotting module."""

from src.experiments.trainer import ModelTrainer, EvaluationMetrics
from src.experiments.benchmark import run_full_benchmark, evaluate_classical_baseline
from src.experiments.ablation import run_feature_ablation_study
from src.experiments.scalability import run_scalability_benchmark
from src.experiments.plotter import (
    plot_benchmark_comparison,
    plot_feature_ablation,
    plot_scalability_curves,
)

__all__ = [
    "ModelTrainer",
    "EvaluationMetrics",
    "run_full_benchmark",
    "evaluate_classical_baseline",
    "run_feature_ablation_study",
    "run_scalability_benchmark",
    "plot_benchmark_comparison",
    "plot_feature_ablation",
    "plot_scalability_curves",
]
