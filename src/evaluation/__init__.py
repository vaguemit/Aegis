"""Evaluation and data integrity audit module."""

from src.evaluation.data_leakage_check import audit_graph_splits_for_leakage

__all__ = ["audit_graph_splits_for_leakage"]
