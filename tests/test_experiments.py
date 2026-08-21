"""
Unit Tests for AegisPath Experiment and Benchmark Pipelines.
Verifies training loop execution, evaluation metrics, ablation formatting,
and scalability benchmarking.
"""

import pytest
import torch
from torch.utils.data import DataLoader

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.experiments.trainer import ModelTrainer, EvaluationMetrics
from src.experiments.scalability import run_scalability_benchmark


@pytest.fixture
def mock_dataloader():
    generator = SyntheticEnterpriseGenerator(
        num_computers=10, num_servers=3, num_users=15, seed=42
    )
    raw_graphs = [generator.generate() for _ in range(4)]
    dataset = [(g.adj_tensor, g.x_matrix, g.y_matrix) for g in raw_graphs]
    return DataLoader(dataset, batch_size=2, shuffle=False)


class TestExperimentPipeline:
    def test_model_trainer_epoch_and_eval(self, mock_dataloader):
        model = GATModel(in_features=20, hidden_dim=32, out_dim=32, num_heads=2, num_layers=2)
        trainer = ModelTrainer(model, learning_rate=1e-3)

        loss = trainer.train_epoch(mock_dataloader)
        assert isinstance(loss, float)
        assert loss >= 0.0

        metrics = trainer.evaluate(mock_dataloader)
        assert isinstance(metrics, EvaluationMetrics)
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1 <= 1.0
        assert 0.0 <= metrics.roc_auc <= 1.0

    def test_scalability_micro_benchmark(self):
        # Quick 2-scale test
        results = run_scalability_benchmark(node_scales=[20, 40])
        assert len(results) == 2
        for r in results:
            assert r["actual_nodes"] > 0
            assert r["gat_inference_ms"] > 0.0
            assert r["beam_search_ms"] > 0.0
