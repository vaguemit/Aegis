"""
NetworkX and Matplotlib Static Graph Visualizer (Phase 4).
Renders enterprise network graphs, distinguishing normal relations from ground-truth attack paths.
"""

from pathlib import Path
from typing import Optional, Any
import matplotlib.pyplot as plt
import networkx as nx
import torch

from src.data.schema import NetworkGraphData, ENTITY_TYPES, PROPERTY_TO_IDX, SecurityProperty
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.data.pignn_loader import load_pignn_graph


def visualize_graph(
    graph_data: NetworkGraphData,
    output_path: str = "artifacts/graph_sample_visualization.png",
    seed: int = 42,
    max_nodes_to_draw: int = 60,
):
    """
    Renders enterprise network topology with NetworkX and Matplotlib.
    Distinguishes attack path edges (red arrows) from normal network relations (gray lines).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    G = nx.DiGraph()
    num_nodes = min(graph_data.num_nodes, max_nodes_to_draw)

    # Add nodes with attributes
    node_colors = []
    for i in range(num_nodes):
        G.add_node(i, label=graph_data.node_names[i] if graph_data.node_names else f"N{i}")
        if i == graph_data.source_idx:
            node_colors.append("#06B6D4") # Cyan Initial Foothold
        elif i == graph_data.target_idx:
            node_colors.append("#EC4899") # Pink Crown Jewel
        elif graph_data.x_matrix[i, PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]] > 0.5:
            node_colors.append("#F59E0B") # Amber CVE
        else:
            node_colors.append("#64748B") # Slate Standard

    # Add edges
    normal_edges = []
    attack_edges = []

    adj = graph_data.adj_tensor[:num_nodes, :num_nodes]
    y = graph_data.y_matrix[:num_nodes, :num_nodes] if graph_data.y_matrix is not None else None

    for u in range(num_nodes):
        for v in range(num_nodes):
            if adj[u, v].sum() > 0.5:
                G.add_edge(u, v)
                if y is not None and y[u, v] > 0.5:
                    attack_edges.append((u, v))
                else:
                    normal_edges.append((u, v))

    plt.figure(figsize=(10, 8), dpi=120)
    pos = nx.spring_layout(G, seed=seed, k=0.35)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=300, alpha=0.9)

    # Draw normal edges
    nx.draw_networkx_edges(
        G, pos, edgelist=normal_edges, edge_color="#94A3B8", alpha=0.4, arrows=True, arrowsize=8
    )

    # Draw attack-path edges (bold red)
    if attack_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=attack_edges, edge_color="#EF4444", width=2.5, alpha=0.9, arrows=True, arrowsize=12
        )

    # Draw labels
    labels = {i: G.nodes[i]["label"].split("_")[0] for i in range(num_nodes)}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_family="sans-serif")

    plt.title(f"AegisPath Network Topology: {graph_data.graph_id}", fontsize=12, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Graph visualization saved to {output_path}")


if __name__ == "__main__":
    gen = SyntheticEnterpriseGenerator(num_computers=15, num_servers=4, num_users=20, seed=42)
    sample_g = gen.generate(scenario_name="sample_demo_graph")
    visualize_graph(sample_g, "artifacts/graph_sample_visualization.png")
