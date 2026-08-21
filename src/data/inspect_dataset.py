"""
Dataset Investigation and Schema Inspection Script (Phase 2).
Examines raw and extracted Active Directory research graphs,
printing file formats, graph counts, node/edge counts, feature dimensions, and labels.
"""

import json
from pathlib import Path
import torch

from src.data.pignn_loader import PIGNNDataset, get_pignn_dataset_summary


def inspect_and_generate_report(
    data_dir: str = "data/_data_",
    output_report_path: str = "dataset_report.json",
):
    """Inspects dataset and outputs dataset_report.json."""
    print(f"[*] Inspecting dataset at: {data_dir}...")

    summary = get_pignn_dataset_summary(data_dir=data_dir)
    print("\n" + "=" * 60)
    print("           AEGISPATH DATASET INVESTIGATION REPORT")
    print("=" * 60)
    for k, v in summary.items():
        print(f"  {k:<28}: {v}")
    print("=" * 60)

    # Save to dataset_report.json
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[+] Saved dataset report to {output_report_path}")
    return summary


if __name__ == "__main__":
    inspect_and_generate_report()
