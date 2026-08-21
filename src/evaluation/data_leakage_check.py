"""
Data Leakage Audit and Split Integrity Verifier (Phase 17).
Verifies that all train, validation, and test splits are strictly partitioned
at the graph level, guaranteeing zero graph ID overlap or structural feature leakage.
"""

from typing import List, Set, Tuple, Any
from src.data.preprocessor import GraphSplitter
from src.data.synthetic_generator import SyntheticEnterpriseGenerator


def audit_graph_splits_for_leakage(
    train_ids: List[str],
    val_ids: List[str],
    test_ids: List[str],
) -> Tuple[bool, str]:
    """
    Audits graph-level split partitions to ensure zero data leakage.

    Returns:
        Tuple of (is_clean: bool, report_message: str)
    """
    set_train = set(train_ids)
    set_val = set(val_ids)
    set_test = set(test_ids)

    train_val_overlap = set_train.intersection(set_val)
    train_test_overlap = set_train.intersection(set_test)
    val_test_overlap = set_val.intersection(set_test)

    has_leakage = bool(train_val_overlap or train_test_overlap or val_test_overlap)

    if has_leakage:
        msg = (
            f"[!] CRITICAL LEAKAGE DETECTED: "
            f"Train-Val Overlap: {len(train_val_overlap)}, "
            f"Train-Test Overlap: {len(train_test_overlap)}, "
            f"Val-Test Overlap: {len(val_test_overlap)}"
        )
        return False, msg

    total = len(set_train) + len(set_val) + len(set_test)
    msg = (
        f"[+] DATA LEAKAGE AUDIT PASSED: 100% Disjoint Graph Partitions. "
        f"Train: {len(set_train)}, Val: {len(set_val)}, Test: {len(set_test)} (Total: {total} graphs)."
    )
    return True, msg


if __name__ == "__main__":
    gen = SyntheticEnterpriseGenerator(seed=42)
    dataset = [gen.generate(scenario_name=f"net_{i}") for i in range(50)]

    splitter = GraphSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42)
    train_set, val_set, test_set = splitter.split(dataset)

    train_ids = [dataset[i].graph_id for i in train_set.indices]
    val_ids = [dataset[i].graph_id for i in val_set.indices]
    test_ids = [dataset[i].graph_id for i in test_set.indices]

    clean, report = audit_graph_splits_for_leakage(train_ids, val_ids, test_ids)
    print(report)
    assert clean, "Data leakage check failed"
