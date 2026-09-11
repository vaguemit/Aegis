"""
Outsider Node Injection and Threat Modeling Engine.
Simulates scenarios where an insider enterprise asset introduces an unauthorized outsider node
(e.g., rogue laptop, shadow VM, covert reverse SOCKS tunnel) into the Active Directory topology.
Dynamically expands the graph tensor representations to reflect perimeter breaches.
"""

from typing import Dict, List, Optional, Tuple, Any
import copy
import random
import time
import torch

from src.data.schema import (
    NetworkGraphData,
    EntityType,
    EdgeType,
    OperatingSystem,
    SecurityProperty,
    ENTITY_TO_IDX,
    PROPERTY_TO_IDX,
    OS_TO_IDX,
    EDGE_TO_IDX,
    NUM_NODE_FEATURES,
    NUM_EDGE_TYPES,
)
from src.defense.outsider_schema import (
    OutsiderType,
    BridgeMechanism,
    OutsiderNode,
    InsiderBridge,
)


class OutsiderThreatEngine:
    """
    Simulates insider-introduced outsider assets into enterprise graph topologies.
    Handles graph dimension scaling, edge tensor expansion, and anomaly injection.
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def inject_outsider_node(
        self,
        graph_data: NetworkGraphData,
        insider_idx: int,
        outsider_type: OutsiderType = OutsiderType.REVERSE_TUNNEL,
        mechanism: BridgeMechanism = BridgeMechanism.SOCKS_CHISEL_TUNNEL,
        edge_type: EdgeType = EdgeType.CAN_RDP,
        outsider_name: Optional[str] = None,
        is_attacker_foothold: bool = True,
    ) -> Tuple[NetworkGraphData, OutsiderNode, InsiderBridge]:
        """
        Injects a new outsider node connected directly to an insider host.
        Expands X from (N, 20) to (N+1, 20) and A from (N, N, 16) to (N+1, N+1, 16).
        """
        old_n = graph_data.num_nodes
        new_n = old_n + 1
        insider_name = graph_data.node_names[insider_idx] if graph_data.node_names and insider_idx < len(graph_data.node_names) else f"node_{insider_idx}"

        if outsider_name is None:
            type_tag = outsider_type.name.lower().replace("_", "-")
            outsider_name = f"OUTSIDER-{type_tag.upper()}-{old_n}"

        # 1. Build Outsider Feature Vector (20 dimensions)
        outsider_x = torch.zeros((1, NUM_NODE_FEATURES), dtype=torch.float32)
        # Entity type: COMPUTER (index 0)
        outsider_x[0, ENTITY_TO_IDX[EntityType.COMPUTER]] = 1.0
        # Enabled:
        outsider_x[0, PROPERTY_TO_IDX[SecurityProperty.ENABLED]] = 1.0
        # Vulnerable / Unpatched:
        outsider_x[0, PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]] = 1.0
        # If this outsider is the new initial entrypoint / foothold:
        if is_attacker_foothold:
            outsider_x[0, PROPERTY_TO_IDX[SecurityProperty.OWNED]] = 1.0
        # OS: Other/Linux or Unmanaged:
        outsider_x[0, OS_TO_IDX[OperatingSystem.OTHER_LINUX]] = 1.0

        # Expand X
        new_x = torch.cat([graph_data.x_matrix, outsider_x], dim=0)

        # 2. Expand Adjacency Tensor A: (new_n, new_n, 16)
        new_adj = torch.zeros((new_n, new_n, NUM_EDGE_TYPES), dtype=torch.float32)
        new_adj[:old_n, :old_n, :] = graph_data.adj_tensor

        edge_channel = EDGE_TO_IDX[edge_type]
        outsider_idx = old_n

        # Insider introduces outsider (bidirectional or directed link)
        # E.g. Insider -> Outsider (bridge), and Outsider -> Insider (inbound pivot)
        new_adj[insider_idx, outsider_idx, edge_channel] = 1.0
        new_adj[outsider_idx, insider_idx, edge_channel] = 1.0

        # 3. Expand Y Attack Matrix
        new_y = torch.zeros((new_n, new_n), dtype=torch.float32)
        if graph_data.y_matrix is not None:
            new_y[:old_n, :old_n] = graph_data.y_matrix
        if is_attacker_foothold:
            new_y[outsider_idx, insider_idx] = 1.0

        # 4. Expanded Node Names
        new_node_names = list(graph_data.node_names) if graph_data.node_names else [f"node_{i}" for i in range(old_n)]
        new_node_names.append(outsider_name)

        # 5. Metadata Objects
        ip = f"192.168.254.{self.rng.randint(10, 250)}"
        mac = f"52:54:00:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}"

        outsider_meta = OutsiderNode(
            node_id=f"outsider-{outsider_idx:03d}",
            name=outsider_name,
            outsider_type=outsider_type,
            ip_address=ip,
            mac_address=mac,
            introduced_by_node_id=insider_idx,
            introduced_by_node_name=insider_name,
            detection_timestamp=time.time(),
            has_edr_agent=False,
            is_domain_joined=False,
            risk_score=0.92,
            open_ports=[22, 1080, 8080],
            metadata={
                "bridge_mechanism": mechanism.value,
                "process_name": "chisel.exe" if "CHISEL" in mechanism.name else "tunnel_svc.elf",
                "tunnel_port": 1080,
                "vlan_id": 999,
            },
        )

        bridge_meta = InsiderBridge(
            bridge_id=f"bridge-{insider_idx}-{outsider_idx}",
            insider_node_idx=insider_idx,
            outsider_node_idx=outsider_idx,
            insider_name=insider_name,
            outsider_name=outsider_name,
            mechanism=mechanism,
            protocol="TCP/SOCKS5",
            port=1080,
            bytes_transferred=self.rng.randint(50000, 5000000),
            is_active=True,
            severity="CRITICAL",
            mitre_techniques=["T1090", "T1572", "T1200", "T1021"],
            introduced_at=time.time(),
            metadata={"edge_type": edge_type.value},
        )

        # Source index updates if outsider becomes new attacker foothold
        new_source = outsider_idx if is_attacker_foothold else graph_data.source_idx

        new_graph = NetworkGraphData(
            graph_id=f"{graph_data.graph_id}_with_outsider",
            num_nodes=new_n,
            x_matrix=new_x,
            adj_tensor=new_adj,
            y_matrix=new_y,
            node_names=new_node_names,
            source_idx=new_source,
            target_idx=graph_data.target_idx,
        )

        return new_graph, outsider_meta, bridge_meta

    def inject_random_outsider_threat(
        self,
        graph_data: NetworkGraphData,
    ) -> Tuple[NetworkGraphData, OutsiderNode, InsiderBridge]:
        """Injects an outsider threat into a randomly selected workstation or server."""
        # Find workstation or server candidates
        candidates = []
        for i in range(graph_data.num_nodes):
            if i != graph_data.target_idx:
                name = graph_data.node_names[i].lower() if graph_data.node_names else ""
                if "dc" not in name:
                    candidates.append(i)

        insider_idx = self.rng.choice(candidates) if candidates else 0
        outsider_type = self.rng.choice(list(OutsiderType))
        mechanism = self.rng.choice(list(BridgeMechanism))
        edge_type = self.rng.choice([EdgeType.CAN_RDP, EdgeType.ADMIN_TO, EdgeType.EXECUTE_DCOM])

        return self.inject_outsider_node(
            graph_data=graph_data,
            insider_idx=insider_idx,
            outsider_type=outsider_type,
            mechanism=mechanism,
            edge_type=edge_type,
        )

    def extract_bridges_from_graph(self, graph_data: NetworkGraphData) -> List[Tuple[int, int]]:
        """Identifies edges connecting internal domain nodes to outsider nodes."""
        outsider_indices = graph_data.get_outsider_indices()
        if not outsider_indices:
            return []

        bridges = []
        for out_idx in outsider_indices:
            # Check inbound and outbound connections
            for i in range(graph_data.num_nodes):
                if i not in outsider_indices:
                    # Check if edge exists in any channel
                    if graph_data.adj_tensor[i, out_idx].sum() > 0 or graph_data.adj_tensor[out_idx, i].sum() > 0:
                        bridges.append((i, out_idx))
        return bridges

    def inject_covert_tunnel(
        self,
        graph_data: NetworkGraphData,
        insider_idx: int,
        tunnel_port: int = 1080,
    ) -> Tuple[NetworkGraphData, OutsiderNode, InsiderBridge]:
        """Simulates an insider machine establishing a reverse SOCKS proxy (e.g. Chisel, Ligolo)."""
        insider_name = graph_data.node_names[insider_idx] if graph_data.node_names else f"node_{insider_idx}"
        outsider_name = f"C2-REVERSE-PROXY-{insider_name.upper()}"
        return self.inject_outsider_node(
            graph_data=graph_data,
            insider_idx=insider_idx,
            outsider_type=OutsiderType.REVERSE_TUNNEL,
            mechanism=BridgeMechanism.SOCKS_CHISEL_TUNNEL,
            edge_type=EdgeType.OPEN,
            outsider_name=outsider_name,
        )

    def inject_dual_homed_nic(
        self,
        graph_data: NetworkGraphData,
        insider_idx: int,
    ) -> Tuple[NetworkGraphData, OutsiderNode, InsiderBridge]:
        """Simulates an insider asset connected to both the corporate LAN and an unmanaged external network."""
        insider_name = graph_data.node_names[insider_idx] if graph_data.node_names else f"node_{insider_idx}"
        outsider_name = f"ROGUE-TETHER-{insider_name.upper()}"
        return self.inject_outsider_node(
            graph_data=graph_data,
            insider_idx=insider_idx,
            outsider_type=OutsiderType.ROGUE_WORKSTATION,
            mechanism=BridgeMechanism.DUAL_HOMED_NIC,
            edge_type=EdgeType.ADMIN_TO,
            outsider_name=outsider_name,
        )

    def inject_shadow_vm(
        self,
        graph_data: NetworkGraphData,
        insider_idx: int,
    ) -> Tuple[NetworkGraphData, OutsiderNode, InsiderBridge]:
        """Simulates a rogue hypervisor VM spawned locally inside an insider host."""
        insider_name = graph_data.node_names[insider_idx] if graph_data.node_names else f"node_{insider_idx}"
        outsider_name = f"SHADOW-VM-{insider_name.upper()}"
        return self.inject_outsider_node(
            graph_data=graph_data,
            insider_idx=insider_idx,
            outsider_type=OutsiderType.SHADOW_VM,
            mechanism=BridgeMechanism.VMWARE_SHARED_NAT,
            edge_type=EdgeType.EXECUTE_DCOM,
            outsider_name=outsider_name,
        )
