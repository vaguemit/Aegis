"""
Graph State Store and Model Cache for FastAPI Backend.
Maintains in-memory graph repository, pre-trained GAT model instances,
and fast Cytoscape conversion helpers with human-readable department names.
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


def format_human_friendly_node_name(
    raw_name: Optional[str],
    idx: int,
    entity_name: str,
    is_target: bool,
    is_hv: bool,
    is_vuln: bool,
    is_owned: bool,
) -> str:
    """Ensures every asset has a clear, human-readable department-based name."""
    if raw_name and ("HR-" in raw_name or "Finance-" in raw_name or "Engineering-" in raw_name or "Primary-" in raw_name or "Corporate-" in raw_name):
        return raw_name

    depts = ["HR", "Finance", "Engineering", "Sales", "Executive"]
    dept = depts[idx % len(depts)]

    first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry"]
    last_names = ["Smith", "Jones", "Miller", "Clark", "Davis", "Wilson", "Taylor", "Brown"]
    fn = first_names[idx % len(first_names)]
    ln = last_names[(idx // len(first_names)) % len(last_names)]

    if entity_name in ["DomainController", "Domain"] or (is_target and is_hv):
        if idx == 0 or is_target:
            return "Primary-Domain-Controller"
        return f"Backup-DC-Enterprise-{idx:02d}"

    if entity_name == "Computer":
        if is_target:
            return "Customer-SQL-Database"
        if is_hv:
            servers = ["Corporate-Web-Portal", "Customer-SQL-Database", "Payroll-DB-Server", "Internal-File-Share", "Payment-Gateway-Host"]
            return servers[idx % len(servers)]
        if is_owned:
            return f"HR-Workstation-01"
        return f"{dept}-Workstation-{idx+1:02d}"

    if entity_name == "User":
        if is_hv:
            return f"Admin.{fn}.{ln} (Enterprise Admin)"
        return f"{fn}.{ln} ({dept})"

    if entity_name == "Group":
        if is_hv or is_target:
            return "Domain-Administrators"
        return f"{dept}-Operators-Group"

    if entity_name == "OU":
        return f"OU-{dept}-Subnet"

    if entity_name == "GPO":
        return f"Policy-GPO-{dept}"

    return f"{dept}-Asset-{idx+1:02d}"


class BackendGraphManager:
    """Singleton-style manager holding active graphs and cached neural models."""

    def __init__(self):
        self.graphs: Dict[str, NetworkGraphData] = {}
        self.models: Dict[str, Any] = {}
        self._init_models()
        self._init_default_graphs()

    def _init_models(self):
        """Initializes GNN model instances and loads trained weights if present."""
        self.models["gat"] = GATModel(in_features=20, hidden_dim=128, out_dim=128, num_heads=4, num_layers=3)
        self.models["gcn"] = GCNModel(in_features=20, hidden_dim=128, out_dim=128, num_layers=3)
        self.models["graphsage"] = GraphSAGEModel(in_features=20, hidden_dim=128, out_dim=128, num_layers=3)
        self.models["dijkstra"] = DijkstraShortestPathBaseline()
        self.models["cvss"] = CVSSWeightedShortestPathBaseline()

        checkpoint_path = Path("checkpoints/best_gat_weights.pt")
        if checkpoint_path.exists():
            try:
                state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
                self.models["gat"].load_state_dict(state_dict, strict=False)
                print(f"[+] Successfully loaded trained GAT weights from {checkpoint_path}")
            except Exception as e:
                print(f"[!] Initializing GAT default weights ({e})")

        for m in self.models.values():
            if hasattr(m, "eval"):
                m.eval()

    def _init_default_graphs(self):
        """Loads curated enterprise demo environments first, followed by research benchmark graphs."""
        # 1. Synthesize curated realistic department enterprise topologies FIRST
        gen_corp = SyntheticEnterpriseGenerator(
            num_computers=24, num_servers=6, num_users=30, num_ous=4, seed=42
        )
        g_corp = gen_corp.generate(scenario_name="demo_corporate_enterprise_60n")
        self.graphs[g_corp.graph_id] = g_corp

        gen_small = SyntheticEnterpriseGenerator(
            num_computers=15, num_servers=4, num_users=20, num_ous=3, seed=101
        )
        g_small = gen_small.generate(scenario_name="demo_enterprise_small_39n")
        self.graphs[g_small.graph_id] = g_small

        gen_med = SyntheticEnterpriseGenerator(
            num_computers=50, num_servers=10, num_users=80, num_ous=5, seed=202
        )
        g_med = gen_med.generate(scenario_name="demo_enterprise_medium_140n")
        self.graphs[g_med.graph_id] = g_med

        # 2. Check for extracted PIGNN benchmark graphs
        pignn_dir = Path("data/_data_")
        if not pignn_dir.exists():
            pignn_dir = Path("replication_pkg/Physics-Informed-GNN (PIGNN)/_Preprocessing_/_data_")

        if pignn_dir.exists():
            pt_files = sorted(list(pignn_dir.glob("*.pt")))[:10]
            for p in pt_files:
                try:
                    g = load_pignn_graph(p, target_dim=20)
                    self.graphs[g.graph_id] = g
                except Exception as e:
                    print(f"[!] Warning loading {p}: {e}")

    def list_graph_summaries(self) -> List[GraphSummary]:
        """Returns metadata summary for all available graphs."""
        summaries = []
        for g_id, g in self.graphs.items():
            vuln_col = PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]
            hv_col = PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]

            vuln_count = int((g.x_matrix[:, vuln_col] > 0.5).sum().item())
            hv_count = int((g.x_matrix[:, hv_col] > 0.5).sum().item())
            edge_count = int((g.adj_tensor > 0.5).sum().item())

            summaries.append(
                GraphSummary(
                    graph_id=g_id,
                    num_nodes=g.num_nodes,
                    num_edges=edge_count,
                    num_vulnerable_nodes=vuln_count,
                    num_high_value_nodes=hv_count,
                )
            )
        return summaries

    def get_graph(self, graph_id: str) -> Optional[NetworkGraphData]:
        return self.graphs.get(graph_id)

    def add_synthetic_graph(self, graph_data: NetworkGraphData) -> str:
        """Stores a newly generated synthetic graph in the repository."""
        self.graphs[graph_data.graph_id] = graph_data
        return graph_data.graph_id

    def get_graph_detail(self, graph_id: str) -> Optional[GraphDetailResponse]:
        """Converts graph into Cytoscape-ready node and edge elements with enriched names."""
        g = self.get_graph(graph_id)
        if g is None:
            return None

        node_elements: List[NodeElement] = []
        for i in range(g.num_nodes):
            x_vec = g.x_matrix[i]
            entity_idx = int(torch.argmax(x_vec[:len(ENTITY_TYPES)]).item())
            entity_name = ENTITY_TYPES[entity_idx].value

            is_enabled = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.ENABLED]].item() > 0.5)
            has_spn = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.HAS_SPN]].item() > 0.5)
            is_hv = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]].item() > 0.5)
            is_vuln = bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]].item() > 0.5)
            is_target = (i == g.target_idx) or bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.TARGET]].item() > 0.5)
            is_owned = (i == g.source_idx) or bool(x_vec[PROPERTY_TO_IDX[SecurityProperty.OWNED]].item() > 0.5)

            raw_name = g.node_names[i] if g.node_names and i < len(g.node_names) else None
            name = format_human_friendly_node_name(
                raw_name=raw_name,
                idx=i,
                entity_name=entity_name,
                is_target=is_target,
                is_hv=is_hv,
                is_vuln=is_vuln,
                is_owned=is_owned,
            )

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


# Global singleton instance for backend routes
graph_manager = BackendGraphManager()
