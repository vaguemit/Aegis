"""
Graph State Store and Model Cache for FastAPI Backend.
Maintains in-memory graph repository, pre-trained GAT model instances,
and fast Cytoscape conversion helpers.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import torch

from src.data.schema import (
    NetworkGraphData,
    ENTITY_TYPES,
    OPERATING_SYSTEMS,
    SECURITY_PROPERTIES,
    SecurityProperty,
    PROPERTY_TO_IDX,
    IDX_TO_EDGE,
    EdgeType,
)
from src.data.pignn_loader import PIGNNDataset, load_pignn_graph
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.models.gat import GATModel
from src.models.gcn import GCNModel
from src.models.graphsage import GraphSAGEModel
from src.models.baselines import DijkstraShortestPathBaseline, CVSSWeightedShortestPathBaseline
from backend.models import (
    GraphSummary,
    NodeElement,
    EdgeElement,
    GraphDetailResponse,
)


class BackendGraphManager:
    """Singleton-style manager holding active graphs and cached neural models."""

    def __init__(self):
        self.graphs: Dict[str, NetworkGraphData] = {}
        self.models: Dict[str, Any] = {}
        self._init_models()
        self._init_default_graphs()

    def _init_models(self):
        """Initializes GNN model instances and loads trained weights if present."""
        self.models["gat"] = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
        self.models["gcn"] = GCNModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
        self.models["graphsage"] = GraphSAGEModel(in_features=20, hidden_dim=64, out_dim=64, num_layers=2)
        self.models["dijkstra"] = DijkstraShortestPathBaseline()
        self.models["cvss"] = CVSSWeightedShortestPathBaseline()

        checkpoint_path = Path("checkpoints/best_gat_weights.pt")
        if checkpoint_path.exists():
            try:
                state_dict = torch.load(checkpoint_path, map_location="cpu")
                self.models["gat"].load_state_dict(state_dict)
                print(f"[+] Successfully loaded trained GAT weights from {checkpoint_path}")
            except Exception as e:
                print(f"[!] Initializing GAT default weights ({e})")

        for m in self.models.values():
            if hasattr(m, "eval"):
                m.eval()

    def _init_default_graphs(self):
        """Loads a few benchmark graphs and synthesizes initial demo enterprise environments."""
        # 1. Check for extracted PIGNN benchmark graphs
        pignn_dir = Path("data/_data_")
        if not pignn_dir.exists():
            pignn_dir = Path("replication_pkg/Physics-Informed-GNN (PIGNN)/_Preprocessing_/_data_")

        if pignn_dir.exists():
            pt_files = sorted(list(pignn_dir.glob("*.pt")))[:5]
            for p in pt_files:
                try:
                    g = load_pignn_graph(p, target_dim=20)
                    self.graphs[g.graph_id] = g
                except Exception as e:
                    print(f"[!] Warning loading {p}: {e}")

        # 2. Synthesize baseline demo enterprise topologies (Small, Medium, Large)
        gen_small = SyntheticEnterpriseGenerator(
            num_computers=20, num_servers=4, num_users=30, num_ous=3, seed=101
        )
        g_small = gen_small.generate(scenario_name="demo_enterprise_small_53n")
        self.graphs[g_small.graph_id] = g_small

        gen_med = SyntheticEnterpriseGenerator(
            num_computers=50, num_servers=10, num_users=80, num_ous=5, seed=202
        )
        g_med = gen_med.generate(scenario_name="demo_enterprise_medium_147n")
        self.graphs[g_med.graph_id] = g_med

    def list_graph_summaries(self) -> List[GraphSummary]:
        """Returns metadata summary for all available graphs."""
        summaries = []
        for g_id, g in self.graphs.items():
            vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
            hv_col = PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]

            num_vuln = int((g.x_matrix[:, vuln_col] > 0.5).sum().item())
            num_hv = int((g.x_matrix[:, hv_col] > 0.5).sum().item())
            num_edges = int((g.adj_tensor.sum(dim=-1) > 0.5).sum().item())

            src_name = g.node_names[g.source_idx] if (g.node_names and g.source_idx is not None) else (f"Node_{g.source_idx}" if g.source_idx is not None else None)
            dst_name = g.node_names[g.target_idx] if (g.node_names and g.target_idx is not None) else (f"Node_{g.target_idx}" if g.target_idx is not None else None)

            summaries.append(
                GraphSummary(
                    graph_id=g_id,
                    num_nodes=g.num_nodes,
                    num_edges=num_edges,
                    num_vulnerable_nodes=num_vuln,
                    num_high_value_nodes=num_hv,
                    source_idx=g.source_idx,
                    target_idx=g.target_idx,
                    source_name=src_name,
                    target_name=dst_name,
                )
            )
        return summaries

    def get_graph(self, graph_id: str) -> Optional[NetworkGraphData]:
        return self.graphs.get(graph_id)

    def get_graph_detail(self, graph_id: str) -> Optional[GraphDetailResponse]:
        """Converts graph into Cytoscape-ready node and edge elements."""
        g = self.get_graph(graph_id)
        if g is None:
            return None

        node_elements: List[NodeElement] = []
        for i in range(g.num_nodes):
            x_vec = g.x_matrix[i]
            # Identify entity type (first 6 features)
            entity_idx = int(torch.argmax(x_vec[:len(ENTITY_TYPES)]).item())
            entity_name = ENTITY_TYPES[entity_idx].value

            is_enabled = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.ENABLED]].item() > 0.5)
            has_spn = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.HAS_SPN]].item() > 0.5)
            is_hv = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]].item() > 0.5)
            is_vuln = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]].item() > 0.5)
            is_target = (i == g.target_idx) or bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.TARGET]].item() > 0.5)
            is_owned = (i == g.source_idx) or bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.OWNED]].item() > 0.5)

            name = g.node_names[i] if g.node_names and i < len(g.node_names) else f"{entity_name}_{i}"

            node_elements.append(
                NodeElement(
                    id=f"n_{i}",
                    index=i,
                    name=name,
                    entity_type=entity_name,
                    is_enabled=is_enabled,
                    has_spn=has_spn,
                    is_high_value=is_hv,
                    is_vulnerable=is_vuln,
                    is_target=is_target,
                    is_owned=is_owned,
                )
            )

        edge_elements: List[EdgeElement] = []
        edge_coords = (g.adj_tensor > 0.5).nonzero(as_tuple=False)
        edge_count = 0

        for coord in edge_coords:
            u = int(coord[0].item())
            v = int(coord[1].item())
            r = int(coord[2].item())
            edge_type_str = IDX_TO_EDGE[r].value
            is_attack = bool(g.y_matrix[u, v].item() > 0.5) if g.y_matrix is not None else False

            edge_elements.append(
                EdgeElement(
                    id=f"e_{u}_{v}_{r}",
                    source=f"n_{u}",
                    target=f"n_{v}",
                    source_idx=u,
                    target_idx=v,
                    edge_type=edge_type_str,
                    is_attack_path=is_attack,
                )
            )
            edge_count += 1

        return GraphDetailResponse(
            graph_id=graph_id,
            num_nodes=g.num_nodes,
            num_edges=edge_count,
            source_idx=g.source_idx,
            target_idx=g.target_idx,
            nodes=node_elements,
            edges=edge_elements,
        )

    def add_synthetic_graph(self, graph_data: NetworkGraphData) -> str:
        """Stores a newly generated synthetic graph in the manager."""
        self.graphs[graph_data.graph_id] = graph_data
        return graph_data.graph_id


# Global Singleton Instance
graph_manager = BackendGraphManager()
