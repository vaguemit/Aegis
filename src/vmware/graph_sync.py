"""
VMware vSphere to AegisPath Graph Topology Synchronizer.
Converts live hypervisor inventory (ESXi hosts, VMs, vSwitches, Portgroups)
into AegisPath NetworkGraphData tensors (X feature matrix, A adjacency tensor, Y ground truth).
"""

from typing import Dict, List, Optional, Tuple, Any
import torch
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import VMwareVMInfo, VMwareDiscoveryReport
from src.vmware.discovery import VMwareTopologyDiscoverer
from src.data.schema import (
    NetworkGraphData,
    NetworkNode,
    EntityType,
    EdgeType,
    OperatingSystem,
    SecurityProperty,
    NUM_NODE_FEATURES,
    NUM_EDGE_TYPES,
    ENTITY_TO_IDX,
    PROPERTY_TO_IDX,
    OS_TO_IDX,
    EDGE_TO_IDX,
)

logger = logging.getLogger("aegispath.vmware.graph_sync")


class VMwareGraphSynchronizer:
    """
    Translates VMware vSphere inventory into AegisPath graph representations for neural path forecasting.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)

    def sync_to_graph_data(self) -> NetworkGraphData:
        """
        Extracts current cluster state and converts into NetworkGraphData.
        """
        report = self.discoverer.discover_cluster()
        vms = report.vms
        n = len(vms)

        # 1. Build X matrix (n, 20)
        x_matrix = torch.zeros((n, NUM_NODE_FEATURES), dtype=torch.float32)
        node_names = []

        dc_idx = 0
        foothold_idx = 0

        for idx, vm in enumerate(vms):
            node_names.append(vm.name)
            name_lower = vm.name.lower()
            is_dc = "dc" in name_lower
            is_server = "srv" in name_lower or "sql" in name_lower or "file" in name_lower or "web" in name_lower or is_dc
            is_rogue = vm.is_outsider or "rogue" in name_lower or "shadow" in name_lower

            # Entity type: COMPUTER
            x_matrix[idx, ENTITY_TO_IDX[EntityType.COMPUTER]] = 1.0

            # Enabled
            x_matrix[idx, PROPERTY_TO_IDX[SecurityProperty.ENABLED]] = 1.0

            # Target / High Value for Domain Controllers
            if is_dc:
                dc_idx = idx
                x_matrix[idx, PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]] = 1.0
                x_matrix[idx, PROPERTY_TO_IDX[SecurityProperty.TARGET]] = 1.0

            # Rogue / Vulnerable / Owned
            if is_rogue:
                foothold_idx = idx
                x_matrix[idx, PROPERTY_TO_IDX[SecurityProperty.OWNED]] = 1.0
                x_matrix[idx, PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]] = 1.0

            # OS mapping
            if "2022" in vm.guest_os or "2019" in vm.guest_os:
                x_matrix[idx, OS_TO_IDX[OperatingSystem.WIN_SERVER_2016_2019]] = 1.0
            elif "11" in vm.guest_os or "10" in vm.guest_os:
                x_matrix[idx, OS_TO_IDX[OperatingSystem.WIN_10]] = 1.0
            else:
                x_matrix[idx, OS_TO_IDX[OperatingSystem.OTHER_LINUX]] = 1.0

        # 2. Build Adjacency Tensor A (n, n, 16)
        adj_tensor = torch.zeros((n, n, NUM_EDGE_TYPES), dtype=torch.float32)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                # Network connectivity based on shared portgroup or standard AD protocols
                vm_i = vms[i]
                vm_j = vms[j]

                # Check if sharing a portgroup
                shared_pg = False
                for nic_i in vm_i.nics:
                    for nic_j in vm_j.nics:
                        if nic_i.portgroup == nic_j.portgroup and nic_i.is_connected and nic_j.is_connected:
                            shared_pg = True
                            break

                if shared_pg:
                    adj_tensor[i, j, EDGE_TO_IDX[EdgeType.CAN_RDP]] = 1.0
                    adj_tensor[i, j, EDGE_TO_IDX[EdgeType.ADMIN_TO]] = 1.0
                    adj_tensor[i, j, EDGE_TO_IDX[EdgeType.OPEN]] = 1.0
                else:
                    # Routed connectivity between workstations and servers
                    if i != j and ("dc" in vm_j.name.lower() or "srv" in vm_j.name.lower()):
                        adj_tensor[i, j, EDGE_TO_IDX[EdgeType.EXECUTE_DCOM]] = 1.0

        # 3. Y attack matrix
        y_matrix = torch.zeros((n, n), dtype=torch.float32)
        # Sequential path from foothold to DC
        if foothold_idx != dc_idx:
            step = 1 if dc_idx > foothold_idx else -1
            curr = foothold_idx
            while curr != dc_idx:
                nxt = curr + step
                y_matrix[curr, nxt] = 1.0
                curr = nxt

        return NetworkGraphData(
            graph_id=f"vmware_synced_cluster_{n}vms",
            num_nodes=n,
            x_matrix=x_matrix,
            adj_tensor=adj_tensor,
            y_matrix=y_matrix,
            node_names=node_names,
            source_idx=foothold_idx,
            target_idx=dc_idx,
        )

    def sync_delta_update(
        self,
        current_graph: NetworkGraphData,
        vm_index: int,
        action: str = "ISOLATE",
    ) -> NetworkGraphData:
        """Applies fast in-place delta updates to graph tensors upon dynamic hypervisor events."""
        new_adj = current_graph.adj_tensor.clone()
        new_y = current_graph.y_matrix.clone() if current_graph.y_matrix is not None else None

        if action == "ISOLATE":
            # Zero out all adjacency channels for this VM
            new_adj[vm_index, :, :] = 0.0
            new_adj[:, vm_index, :] = 0.0
            if new_y is not None:
                new_y[vm_index, :] = 0.0
                new_y[:, vm_index] = 0.0

        return NetworkGraphData(
            graph_id=f"{current_graph.graph_id}_delta_{action.lower()}",
            num_nodes=current_graph.num_nodes,
            x_matrix=current_graph.x_matrix.clone(),
            adj_tensor=new_adj,
            y_matrix=new_y,
            node_names=list(current_graph.node_names) if current_graph.node_names else None,
            source_idx=current_graph.source_idx,
            target_idx=current_graph.target_idx,
        )
