"""
Experiment 4: Scalability Benchmark.
Evaluates AegisPath performance across synthetic networks of scale 20, 50, 100, 250, 500, and 1000 nodes.
Measures Graph Generation Latency, GAT Inference Latency, Constrained Beam Search Latency,
and Peak Memory Consumption.
"""

from typing import Dict, List, Any
import gc
import time
import torch

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.search.beam_search import ConstrainedBeamSearch


def run_scalability_benchmark(
    node_scales: List[int] = [20, 50, 100, 250, 500, 1000],
) -> List[Dict[str, Any]]:
    """Runs scalability tests across network sizes."""
    print("[*] Starting AegisPath Enterprise Scalability Benchmark...")
    results = []

    model = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
    model.eval()
    beam_searcher = ConstrainedBeamSearch(beam_width=3, max_hops=12)

    for n in node_scales:
        # Scale component counts proportionally
        num_computers = max(5, int(n * 0.45))
        num_servers = max(2, int(n * 0.10))
        num_users = max(10, int(n * 0.40))
        num_ous = max(2, int(n * 0.03))
        num_dcs = max(1, int(n * 0.02))

        # 1. Measure Graph Generation Time
        t0 = time.perf_counter()
        generator = SyntheticEnterpriseGenerator(
            num_computers=num_computers,
            num_servers=num_servers,
            num_users=num_users,
            num_ous=num_ous,
            num_domain_controllers=num_dcs,
            seed=42,
        )
        graph_data = generator.generate()
        t1 = time.perf_counter()
        gen_time_ms = (t1 - t0) * 1000.0

        actual_nodes = graph_data.num_nodes
        num_edges = int((graph_data.adj_tensor.sum(dim=-1) > 0.5).sum().item())

        # 2. Measure GAT Forward Inference Latency
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        inference_times = []
        with torch.no_grad():
            for _ in range(5):
                t_inf_0 = time.perf_counter()
                edge_probs = model(graph_data.x_matrix, graph_data.adj_tensor)
                t_inf_1 = time.perf_counter()
                inference_times.append((t_inf_1 - t_inf_0) * 1000.0)
        avg_inf_ms = float(sum(inference_times) / len(inference_times))

        # 3. Measure Constrained Beam Search Latency
        t_bs_0 = time.perf_counter()
        paths = beam_searcher.search(
            edge_probs=edge_probs,
            adj_tensor=graph_data.adj_tensor,
            x_matrix=graph_data.x_matrix,
            source_idx=graph_data.source_idx,
            target_idx=graph_data.target_idx,
            node_names=graph_data.node_names,
            top_k=3,
        )
        t_bs_1 = time.perf_counter()
        bs_time_ms = (t_bs_1 - t_bs_0) * 1000.0

        top_confidence = paths[0].confidence_score if paths else 0.0
        hop_count = paths[0].hop_count if paths else 0

        # Estimate memory for tensors (approx MB)
        tensor_bytes = (
            graph_data.adj_tensor.element_size() * graph_data.adj_tensor.nelement()
            + graph_data.x_matrix.element_size() * graph_data.x_matrix.nelement()
            + graph_data.y_matrix.element_size() * graph_data.y_matrix.nelement()
        )
        approx_mem_mb = tensor_bytes / (1024 * 1024)

        record = {
            "scale_target": n,
            "actual_nodes": actual_nodes,
            "num_edges": num_edges,
            "generation_time_ms": gen_time_ms,
            "gat_inference_ms": avg_inf_ms,
            "beam_search_ms": bs_time_ms,
            "total_latency_ms": avg_inf_ms + bs_time_ms,
            "approx_mem_mb": approx_mem_mb,
            "top_confidence": top_confidence,
            "hop_count": hop_count,
        }
        results.append(record)

        print(
            f"[+] Scale ~{n:>4d} nodes | Actual: {actual_nodes:>4d} nodes, {num_edges:>5d} edges | "
            f"GAT: {avg_inf_ms:>6.2f}ms | BeamSearch: {bs_time_ms:>6.2f}ms | Mem: {approx_mem_mb:>6.2f}MB"
        )

    print("\n" + "=" * 95)
    print("                       AEGISPATH SCALABILITY BENCHMARK")
    print("=" * 95)
    print(f"{'Nodes':<8} | {'Edges':<8} | {'GAT Inf (ms)':<14} | {'BeamSearch (ms)':<16} | {'Total Latency (ms)':<20} | {'Mem (MB)':<10}")
    print("-" * 95)
    for r in results:
        print(
            f"{r['actual_nodes']:<8d} | "
            f"{r['num_edges']:<8d} | "
            f"{r['gat_inference_ms']:>12.2f}ms | "
            f"{r['beam_search_ms']:>14.2f}ms | "
            f"{r['total_latency_ms']:>18.2f}ms | "
            f"{r['approx_mem_mb']:>8.2f}MB"
        )
    print("=" * 95)

    return results


if __name__ == "__main__":
    run_scalability_benchmark()
