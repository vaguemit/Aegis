"""
Synthetic Enterprise Network & Attack Scenario Generator.
Generates realistic, configurable Active Directory enterprise networks with
subnets, organizational units, computers, domain controllers, privilege links,
vulnerability distributions, and ground-truth multi-hop attack paths.
"""

import random
from typing import Dict, List, Optional, Tuple, Set, Any
import numpy as np
import torch

from src.data.schema import (
    EntityType,
    EdgeType,
    OperatingSystem,
    SecurityProperty,
    NetworkNode,
    NetworkEdge,
    NetworkGraphData,
    NUM_NODE_FEATURES,
    NUM_EDGE_TYPES,
    EDGE_TO_IDX,
    PROPERTY_TO_IDX,
)


class SyntheticEnterpriseGenerator:
    """
    Parametric synthetic generator for enterprise Active Directory topologies.
    Produces both small laboratory graphs (20-50 nodes) and enterprise-scale networks (500-1000+ nodes).
    """

    def __init__(
        self,
        num_computers: int = 40,
        num_servers: int = 10,
        num_users: int = 80,
        num_ous: int = 5,
        num_gpos: int = 4,
        num_domain_controllers: int = 2,
        cve_probability: float = 0.25,
        spn_probability: float = 0.15,
        seed: Optional[int] = None,
    ):
        self.num_computers = num_computers
        self.num_servers = num_servers
        self.num_users = num_users
        self.num_ous = num_ous
        self.num_gpos = num_gpos
        self.num_domain_controllers = num_domain_controllers
        self.cve_probability = cve_probability
        self.spn_probability = spn_probability
        self.seed = seed

        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
            torch.manual_seed(self.seed)

    def generate(self, scenario_name: Optional[str] = None) -> NetworkGraphData:
        """
        Generates a complete enterprise graph with nodes, multi-relational edges,
        and a validated ground-truth lateral movement attack path.
        """
        nodes: List[NetworkNode] = []
        edges: List[NetworkEdge] = []
        node_id_counter = 0

        # 1. Create Domain Root Node
        domain_node = NetworkNode(
            node_id=node_id_counter,
            name="CORP.LOCAL",
            entity_type=EntityType.DOMAIN,
            is_high_value=True,
        )
        nodes.append(domain_node)
        domain_idx = node_id_counter
        node_id_counter += 1

        # 2. Create Domain Controllers
        dc_indices = []
        for i in range(self.num_domain_controllers):
            dc_node = NetworkNode(
                node_id=node_id_counter,
                name=f"DC{i+1:02d}.CORP.LOCAL",
                entity_type=EntityType.COMPUTER,
                os=OperatingSystem.WIN_SERVER_2016_2019,
                is_high_value=True,
                is_target=(i == 0), # Primary DC is crown jewel target
            )
            nodes.append(dc_node)
            dc_indices.append(node_id_counter)
            # Domain Contains DC
            edges.append(NetworkEdge(domain_idx, node_id_counter, EdgeType.CONTAINS))
            node_id_counter += 1

        # 3. Create Organizational Units (OUs)
        ou_names = ["Executive", "Finance", "HumanResources", "Engineering", "Operations", "Sales", "IT_Admin"]
        ou_indices = []
        for i in range(self.num_ous):
            name = ou_names[i % len(ou_names)] if i < len(ou_names) else f"OU_Sub_{i+1}"
            ou_node = NetworkNode(
                node_id=node_id_counter,
                name=f"OU={name},DC=CORP,DC=LOCAL",
                entity_type=EntityType.OU,
            )
            nodes.append(ou_node)
            ou_indices.append(node_id_counter)
            edges.append(NetworkEdge(domain_idx, node_id_counter, EdgeType.CONTAINS))
            node_id_counter += 1

        # 4. Create Group Policy Objects (GPOs)
        gpo_indices = []
        for i in range(self.num_gpos):
            gpo_node = NetworkNode(
                node_id=node_id_counter,
                name=f"Default_Policy_GPO_{i+1}",
                entity_type=EntityType.GPO,
            )
            nodes.append(gpo_node)
            gpo_indices.append(node_id_counter)
            # Link GPO to random OU
            target_ou = random.choice(ou_indices)
            edges.append(NetworkEdge(target_ou, node_id_counter, EdgeType.GP_LINK))
            node_id_counter += 1

        # 5. Create Core Security Groups
        group_names = ["Domain Admins", "Server Operators", "HelpDesk", "Workstation Admins", "Standard Users"]
        group_indices: Dict[str, int] = {}
        for g_name in group_names:
            is_hv = g_name in ["Domain Admins", "Server Operators"]
            g_node = NetworkNode(
                node_id=node_id_counter,
                name=g_name,
                entity_type=EntityType.GROUP,
                is_high_value=is_hv,
                is_target=(g_name == "Domain Admins"),
            )
            nodes.append(g_node)
            group_indices[g_name] = node_id_counter
            # Domain contains groups
            edges.append(NetworkEdge(domain_idx, node_id_counter, EdgeType.CONTAINS))
            node_id_counter += 1

        # Domain Admins have AdminTo / DCSync on Domain & DCs
        da_idx = group_indices["Domain Admins"]
        for dc_idx in dc_indices:
            edges.append(NetworkEdge(da_idx, dc_idx, EdgeType.ADMIN_TO))
            edges.append(NetworkEdge(da_idx, dc_idx, EdgeType.GENERIC_ALL))
        edges.append(NetworkEdge(da_idx, domain_idx, EdgeType.DC_SYNC))
        edges.append(NetworkEdge(da_idx, domain_idx, EdgeType.GET_CHANGES_ALL))

        # 6. Create Servers
        server_indices = []
        server_types = ["WEB_SRV", "DB_SQL", "FILE_SHARE", "APP_SRV", "AUTH_PROXY"]
        server_os_list = [OperatingSystem.WIN_SERVER_2012, OperatingSystem.WIN_SERVER_2016_2019, OperatingSystem.OTHER_LINUX]
        for i in range(self.num_servers):
            srv_type = server_types[i % len(server_types)]
            is_vuln = (random.random() < self.cve_probability)
            srv_node = NetworkNode(
                node_id=node_id_counter,
                name=f"{srv_type}_{i+1:02d}",
                entity_type=EntityType.COMPUTER,
                os=random.choice(server_os_list),
                is_vulnerable=is_vuln,
                is_high_value=(srv_type in ["DB_SQL", "AUTH_PROXY"]),
            )
            nodes.append(srv_node)
            server_indices.append(node_id_counter)
            # Assign server to OU
            ou_idx = random.choice(ou_indices)
            edges.append(NetworkEdge(ou_idx, node_id_counter, EdgeType.CONTAINS))
            # Server Operators are AdminTo Servers
            edges.append(NetworkEdge(group_indices["Server Operators"], node_id_counter, EdgeType.ADMIN_TO))
            # Server Operators has GenericAll on servers
            edges.append(NetworkEdge(group_indices["Server Operators"], node_id_counter, EdgeType.GENERIC_ALL))
            node_id_counter += 1

        # 7. Create Client Workstations
        workstation_indices = []
        client_os_list = [OperatingSystem.WIN_10, OperatingSystem.WIN_7]
        for i in range(self.num_computers):
            is_vuln = (random.random() < self.cve_probability)
            ws_node = NetworkNode(
                node_id=node_id_counter,
                name=f"WS_{i+1:03d}",
                entity_type=EntityType.COMPUTER,
                os=random.choice(client_os_list),
                is_vulnerable=is_vuln,
            )
            nodes.append(ws_node)
            workstation_indices.append(node_id_counter)
            ou_idx = random.choice(ou_indices)
            edges.append(NetworkEdge(ou_idx, node_id_counter, EdgeType.CONTAINS))
            # Workstation Admins / HelpDesk have CanRDP & AdminTo
            edges.append(NetworkEdge(group_indices["Workstation Admins"], node_id_counter, EdgeType.ADMIN_TO))
            edges.append(NetworkEdge(group_indices["HelpDesk"], node_id_counter, EdgeType.CAN_RDP))
            node_id_counter += 1

        # 8. Create Users
        user_indices = []
        for i in range(self.num_users):
            is_admin = (i < 3) # Top 3 are Domain Admins
            is_srv_admin = (3 <= i < 8) # Next 5 are Server Operators
            is_helpdesk = (8 <= i < 14) # Helpdesk staff
            has_spn = (random.random() < self.spn_probability) and not is_admin

            u_name = f"user_{i+1:03d}"
            if is_admin:
                u_name = f"admin_{i+1:02d}"
            elif is_srv_admin:
                u_name = f"srvadmin_{i-2:02d}"

            u_node = NetworkNode(
                node_id=node_id_counter,
                name=u_name,
                entity_type=EntityType.USER,
                has_spn=has_spn,
                is_high_value=is_admin,
            )
            nodes.append(u_node)
            user_idx = node_id_counter
            user_indices.append(user_idx)

            # Assign to OU
            ou_idx = random.choice(ou_indices)
            edges.append(NetworkEdge(ou_idx, user_idx, EdgeType.CONTAINS))

            # Group memberships
            if is_admin:
                edges.append(NetworkEdge(user_idx, group_indices["Domain Admins"], EdgeType.MEMBER_OF))
            elif is_srv_admin:
                edges.append(NetworkEdge(user_idx, group_indices["Server Operators"], EdgeType.MEMBER_OF))
            elif is_helpdesk:
                edges.append(NetworkEdge(user_idx, group_indices["HelpDesk"], EdgeType.MEMBER_OF))
            else:
                edges.append(NetworkEdge(user_idx, group_indices["Standard Users"], EdgeType.MEMBER_OF))

            # HasSession relationships (users logged in on workstations)
            if workstation_indices:
                assigned_ws = random.choice(workstation_indices)
                edges.append(NetworkEdge(assigned_ws, user_idx, EdgeType.HAS_SESSION))

            node_id_counter += 1

        # 9. Synthesize Ground-Truth Attack Path (Source -> Target)
        # Select initial foothold (standard workstation / low-priv user)
        foothold_ws = workstation_indices[0] if workstation_indices else 0
        nodes[foothold_ws].is_owned = True

        # Target is Primary DC or Domain Admin
        target_node_idx = dc_indices[0] if dc_indices else domain_idx
        nodes[target_node_idx].is_target = True

        # Construct realistic tactical lateral movement path:
        # Foothold WS -> Local User Session -> Pivoting to Vulnerable Server -> Compromising Server Admin -> Domain Admin -> Domain Controller
        path_sequence = self._construct_tactical_attack_path(
            nodes=nodes,
            edges=edges,
            foothold_idx=foothold_ws,
            target_idx=target_node_idx,
            workstation_indices=workstation_indices,
            server_indices=server_indices,
            user_indices=user_indices,
            group_indices=group_indices,
        )

        # 10. Build Numerical Matrices & Tensors
        num_total_nodes = len(nodes)
        x_matrix = torch.zeros((num_total_nodes, NUM_NODE_FEATURES), dtype=torch.float32)
        adj_tensor = torch.zeros((num_total_nodes, num_total_nodes, NUM_EDGE_TYPES), dtype=torch.float32)
        y_matrix = torch.zeros((num_total_nodes, num_total_nodes), dtype=torch.float32)

        for i, node in enumerate(nodes):
            x_matrix[i] = node.to_feature_vector()

        for edge in edges:
            e_idx = EDGE_TO_IDX[edge.edge_type]
            adj_tensor[edge.source_idx, edge.target_idx, e_idx] = 1.0

        # Mark ground-truth edges in Y
        for hop in range(len(path_sequence) - 1):
            u = path_sequence[hop]
            v = path_sequence[hop + 1]
            y_matrix[u, v] = 1.0

        graph_id = scenario_name or f"syn_net_{num_total_nodes}n_{len(edges)}e"
        node_names = [n.name for n in nodes]

        return NetworkGraphData(
            graph_id=graph_id,
            num_nodes=num_total_nodes,
            x_matrix=x_matrix,
            adj_tensor=adj_tensor,
            y_matrix=y_matrix,
            node_names=node_names,
            source_idx=foothold_ws,
            target_idx=target_node_idx,
            attack_path_nodes=path_sequence,
        )

    def _construct_tactical_attack_path(
        self,
        nodes: List[NetworkNode],
        edges: List[NetworkEdge],
        foothold_idx: int,
        target_idx: int,
        workstation_indices: List[int],
        server_indices: List[int],
        user_indices: List[int],
        group_indices: Dict[str, int],
    ) -> List[int]:
        """Synthesizes a realistic multi-hop attack chain and ensures supporting edges exist."""
        path: List[int] = [foothold_idx]

        # Step 1: Find user session on foothold
        user_on_ws = None
        for edge in edges:
            if edge.source_idx == foothold_idx and edge.edge_type == EdgeType.HAS_SESSION:
                user_on_ws = edge.target_idx
                break
        if user_on_ws is None:
            user_on_ws = user_indices[-1] if user_indices else foothold_idx
            edges.append(NetworkEdge(foothold_idx, user_on_ws, EdgeType.HAS_SESSION))
        path.append(user_on_ws)

        # Step 2: User exploits / logs in on an intermediate Pivot Server
        pivot_server = server_indices[0] if server_indices else foothold_idx
        nodes[pivot_server].is_vulnerable = True
        edges.append(NetworkEdge(user_on_ws, pivot_server, EdgeType.OPEN)) # Exploitation
        path.append(pivot_server)

        # Step 3: High-privilege Server Admin is logged in on Pivot Server
        srv_admin_user = user_indices[3] if len(user_indices) > 3 else user_on_ws
        edges.append(NetworkEdge(pivot_server, srv_admin_user, EdgeType.HAS_SESSION))
        path.append(srv_admin_user)

        # Step 4: Server Admin moves to Domain Admin Group / Domain Controller
        da_group = group_indices["Domain Admins"]
        edges.append(NetworkEdge(srv_admin_user, da_group, EdgeType.MEMBER_OF))
        path.append(da_group)

        # Step 5: Domain Admin compromises Crown Jewel Target (Domain Controller)
        edges.append(NetworkEdge(da_group, target_idx, EdgeType.ADMIN_TO))
        path.append(target_idx)

        return path
