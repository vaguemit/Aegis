"""
Synthetic Enterprise Network & Attack Scenario Generator.
Generates realistic, configurable Active Directory enterprise networks with
subnets, organizational units, computers, domain controllers, privilege links,
vulnerability distributions, and ground-truth multi-hop attack paths.
Supports exact node count and edge density control.
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
    Produces customizable graphs (15 to 1,000+ nodes) with fine-grained edge density control.
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
        target_nodes: Optional[int] = None,
        target_edges: Optional[int] = None,
        edge_multiplier: Optional[float] = None,
        seed: Optional[int] = None,
    ):
        self.target_nodes = target_nodes
        self.target_edges = target_edges
        self.edge_multiplier = edge_multiplier

        if target_nodes is not None:
            # Dynamically partition target_nodes into realistic AD components
            target_n = max(15, target_nodes)
            dc_count = max(1, int(target_n * 0.04))
            ou_count = max(2, int(target_n * 0.06))
            gpo_count = max(2, int(target_n * 0.05))
            groups_count = 5
            domain_count = 1

            overhead = domain_count + dc_count + ou_count + gpo_count + groups_count
            remaining = max(5, target_n - overhead)

            srv_count = max(2, int(remaining * 0.20))
            ws_count = max(2, int(remaining * 0.45))
            usr_count = max(1, remaining - (srv_count + ws_count))

            self.num_domain_controllers = dc_count
            self.num_ous = ou_count
            self.num_gpos = gpo_count
            self.num_servers = srv_count
            self.num_computers = ws_count
            self.num_users = usr_count
        else:
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
        existing_edge_set: Set[Tuple[int, int, EdgeType]] = set()

        def add_edge_safe(u: int, v: int, etype: EdgeType) -> bool:
            if u == v:
                return False
            key = (u, v, etype)
            if key not in existing_edge_set:
                existing_edge_set.add(key)
                edges.append(NetworkEdge(u, v, etype))
                return True
            return False

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
        dc_titles = ["Primary-Domain-Controller", "Backup-DC-Enterprise", "Branch-DC-Internal"]
        for i in range(self.num_domain_controllers):
            dc_name = dc_titles[i % len(dc_titles)] if i < len(dc_titles) else f"Domain-Controller-{i+1:02d}"
            dc_node = NetworkNode(
                node_id=node_id_counter,
                name=dc_name,
                entity_type=EntityType.COMPUTER,
                os=OperatingSystem.WIN_SERVER_2016_2019,
                is_high_value=True,
                is_target=(i == 0),
            )
            nodes.append(dc_node)
            dc_indices.append(node_id_counter)
            add_edge_safe(domain_idx, node_id_counter, EdgeType.CONTAINS)
            node_id_counter += 1

        # 3. Create Organizational Units (OUs)
        ou_names = ["Executive-Leadership", "Finance-Dept", "HR-Operations", "Engineering-Core", "IT-Infrastructure", "Sales-Marketing"]
        ou_indices = []
        for i in range(self.num_ous):
            name = ou_names[i % len(ou_names)] if i < len(ou_names) else f"Subnet-OU-{i+1}"
            ou_node = NetworkNode(
                node_id=node_id_counter,
                name=f"OU-{name}",
                entity_type=EntityType.OU,
            )
            nodes.append(ou_node)
            ou_indices.append(node_id_counter)
            add_edge_safe(domain_idx, node_id_counter, EdgeType.CONTAINS)
            node_id_counter += 1

        # 4. Create Group Policy Objects (GPOs)
        gpo_indices = []
        gpo_titles = ["Password-Policy-GPO", "Firewall-Rule-GPO", "Endpoint-Security-GPO", "Audit-Log-GPO"]
        for i in range(self.num_gpos):
            gpo_name = gpo_titles[i % len(gpo_titles)] if i < len(gpo_titles) else f"Policy-GPO-{i+1}"
            gpo_node = NetworkNode(
                node_id=node_id_counter,
                name=gpo_name,
                entity_type=EntityType.GPO,
            )
            nodes.append(gpo_node)
            gpo_indices.append(node_id_counter)
            target_ou = random.choice(ou_indices)
            add_edge_safe(target_ou, node_id_counter, EdgeType.GP_LINK)
            node_id_counter += 1

        # 5. Create Core Security Groups
        group_names = ["Domain-Administrators", "Server-Operators-Group", "IT-HelpDesk-Admins", "Workstation-Admins", "Standard-Corporate-Users"]
        group_indices: Dict[str, int] = {}
        for g_name in group_names:
            is_hv = g_name in ["Domain-Administrators", "Server-Operators-Group"]
            g_node = NetworkNode(
                node_id=node_id_counter,
                name=g_name,
                entity_type=EntityType.GROUP,
                is_high_value=is_hv,
                is_target=(g_name == "Domain-Administrators"),
            )
            nodes.append(g_node)
            group_indices[g_name] = node_id_counter
            add_edge_safe(domain_idx, node_id_counter, EdgeType.CONTAINS)
            node_id_counter += 1

        da_idx = group_indices["Domain-Administrators"]
        for dc_idx in dc_indices:
            add_edge_safe(da_idx, dc_idx, EdgeType.ADMIN_TO)
            add_edge_safe(da_idx, dc_idx, EdgeType.GENERIC_ALL)
        add_edge_safe(da_idx, domain_idx, EdgeType.DC_SYNC)
        add_edge_safe(da_idx, domain_idx, EdgeType.GET_CHANGES_ALL)

        # 6. Create Servers
        server_indices = []
        server_types = [
            "Corporate-Web-Portal",
            "Customer-SQL-Database",
            "Payroll-DB-Server",
            "Internal-File-Share",
            "VPN-Auth-Proxy",
            "App-Server-Production",
            "GitLab-Build-Server",
            "Payment-Gateway-Host",
        ]
        server_os_list = [OperatingSystem.WIN_SERVER_2012, OperatingSystem.WIN_SERVER_2016_2019, OperatingSystem.OTHER_LINUX]
        for i in range(self.num_servers):
            srv_type = server_types[i % len(server_types)]
            is_vuln = (random.random() < self.cve_probability)
            srv_name = f"{srv_type}-{i+1:02d}" if i >= len(server_types) else srv_type
            srv_node = NetworkNode(
                node_id=node_id_counter,
                name=srv_name,
                entity_type=EntityType.COMPUTER,
                os=random.choice(server_os_list),
                is_vulnerable=is_vuln,
                is_high_value=("Database" in srv_type or "Payment" in srv_type or "Auth" in srv_type),
            )
            nodes.append(srv_node)
            server_indices.append(node_id_counter)
            ou_idx = random.choice(ou_indices)
            add_edge_safe(ou_idx, node_id_counter, EdgeType.CONTAINS)
            add_edge_safe(group_indices["Server-Operators-Group"], node_id_counter, EdgeType.ADMIN_TO)
            add_edge_safe(group_indices["Server-Operators-Group"], node_id_counter, EdgeType.GENERIC_ALL)
            node_id_counter += 1

        # 7. Create Client Workstations
        workstation_indices = []
        depts = ["Finance", "HR", "Engineering", "Sales", "Executive", "Marketing", "Legal", "DevOps"]
        client_os_list = [OperatingSystem.WIN_10, OperatingSystem.WIN_7]
        for i in range(self.num_computers):
            dept = depts[i % len(depts)]
            is_vuln = (random.random() < self.cve_probability)
            ws_node = NetworkNode(
                node_id=node_id_counter,
                name=f"{dept}-Workstation-{i+1:02d}",
                entity_type=EntityType.COMPUTER,
                os=random.choice(client_os_list),
                is_vulnerable=is_vuln,
            )
            nodes.append(ws_node)
            workstation_indices.append(node_id_counter)
            ou_idx = random.choice(ou_indices)
            add_edge_safe(ou_idx, node_id_counter, EdgeType.CONTAINS)
            add_edge_safe(group_indices["Workstation-Admins"], node_id_counter, EdgeType.ADMIN_TO)
            add_edge_safe(group_indices["IT-HelpDesk-Admins"], node_id_counter, EdgeType.CAN_RDP)
            node_id_counter += 1

        # 8. Create Users
        user_indices = []
        first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Isabella", "Jack", "Karen", "Liam", "Mia", "Noah", "Olivia"]
        last_names = ["Smith", "Jones", "Taylor", "Brown", "Wilson", "Johnson", "Clark", "Davis", "Miller", "White"]
        for i in range(self.num_users):
            is_admin = (i < 2)
            is_srv_admin = (2 <= i < 5)
            is_helpdesk = (5 <= i < 9)
            has_spn = (random.random() < self.spn_probability) and not is_admin

            fn = first_names[i % len(first_names)]
            ln = last_names[(i // len(first_names)) % len(last_names)]
            dept_tag = depts[i % len(depts)]

            if is_admin:
                u_name = f"Admin.{fn}.{ln} (Enterprise Admin)"
            elif is_srv_admin:
                u_name = f"SrvAdmin.{fn}.{ln} (Ops)"
            elif is_helpdesk:
                u_name = f"Support.{fn}.{ln} (IT-HelpDesk)"
            else:
                u_name = f"{fn}.{ln} ({dept_tag})"

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

            ou_idx = random.choice(ou_indices)
            add_edge_safe(ou_idx, user_idx, EdgeType.CONTAINS)

            if is_admin:
                add_edge_safe(user_idx, group_indices["Domain-Administrators"], EdgeType.MEMBER_OF)
            elif is_srv_admin:
                add_edge_safe(user_idx, group_indices["Server-Operators-Group"], EdgeType.MEMBER_OF)
            elif is_helpdesk:
                add_edge_safe(user_idx, group_indices["IT-HelpDesk-Admins"], EdgeType.MEMBER_OF)
            else:
                add_edge_safe(user_idx, group_indices["Standard-Corporate-Users"], EdgeType.MEMBER_OF)

            if workstation_indices:
                assigned_ws = random.choice(workstation_indices)
                add_edge_safe(assigned_ws, user_idx, EdgeType.HAS_SESSION)

            node_id_counter += 1

        # 9. Synthesize Ground-Truth Attack Path (Source -> Target)
        foothold_ws = workstation_indices[0] if workstation_indices else 0
        nodes[foothold_ws].is_owned = True
        target_node_idx = dc_indices[0] if dc_indices else domain_idx
        nodes[target_node_idx].is_target = True

        path_sequence = self._construct_tactical_attack_path(
            nodes=nodes,
            edges=edges,
            add_edge_func=add_edge_safe,
            foothold_idx=foothold_ws,
            target_idx=target_node_idx,
            workstation_indices=workstation_indices,
            server_indices=server_indices,
            user_indices=user_indices,
            group_indices=group_indices,
        )

        # 10. Fine-grained Edge Count & Density Adjustment
        target_e = self.target_edges
        if target_e is None and self.edge_multiplier is not None:
            target_e = int(len(nodes) * self.edge_multiplier)

        if target_e is not None:
            # If we need more edges, add plausible enterprise relations
            while len(edges) < target_e:
                choice_roll = random.random()
                if choice_roll < 0.35 and workstation_indices and server_indices:
                    w = random.choice(workstation_indices)
                    s = random.choice(server_indices)
                    etype = random.choice([EdgeType.CAN_RDP, EdgeType.OPEN, EdgeType.EXECUTE_DCOM])
                    add_edge_safe(w, s, etype)
                elif choice_roll < 0.65 and user_indices and workstation_indices:
                    u = random.choice(user_indices)
                    w = random.choice(workstation_indices)
                    etype = random.choice([EdgeType.ADMIN_TO, EdgeType.CAN_RDP, EdgeType.GENERIC_ALL])
                    add_edge_safe(u, w, etype)
                elif choice_roll < 0.85 and server_indices and len(server_indices) > 1:
                    s1, s2 = random.sample(server_indices, 2)
                    etype = random.choice([EdgeType.EXECUTE_DCOM, EdgeType.OPEN, EdgeType.ALLOWED_TO_DELEGATE])
                    add_edge_safe(s1, s2, etype)
                elif user_indices and server_indices:
                    u = random.choice(user_indices)
                    s = random.choice(server_indices)
                    add_edge_safe(u, s, EdgeType.OPEN)
                else:
                    if len(nodes) > 2:
                        u, v = random.sample(range(len(nodes)), 2)
                        add_edge_safe(u, v, EdgeType.MEMBER_OF)

                # Safeguard against infinite loop if fully saturated
                if len(edges) >= len(nodes) * (len(nodes) - 1):
                    break

        # 11. Build Numerical Matrices & Tensors
        num_total_nodes = len(nodes)
        x_matrix = torch.zeros((num_total_nodes, NUM_NODE_FEATURES), dtype=torch.float32)
        adj_tensor = torch.zeros((num_total_nodes, num_total_nodes, NUM_EDGE_TYPES), dtype=torch.float32)
        y_matrix = torch.zeros((num_total_nodes, num_total_nodes), dtype=torch.float32)

        for i, node in enumerate(nodes):
            x_matrix[i] = node.to_feature_vector()

        for edge in edges:
            e_idx = EDGE_TO_IDX[edge.edge_type]
            adj_tensor[edge.source_idx, edge.target_idx, e_idx] = 1.0

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
        add_edge_func: Any,
        foothold_idx: int,
        target_idx: int,
        workstation_indices: List[int],
        server_indices: List[int],
        user_indices: List[int],
        group_indices: Dict[str, int],
    ) -> List[int]:
        """Synthesizes a realistic multi-hop attack chain and ensures supporting edges exist."""
        path: List[int] = [foothold_idx]

        # Step 1: User session on foothold
        user_on_ws = None
        for edge in edges:
            if edge.source_idx == foothold_idx and edge.edge_type == EdgeType.HAS_SESSION:
                user_on_ws = edge.target_idx
                break
        if user_on_ws is None:
            user_on_ws = user_indices[-1] if user_indices else foothold_idx
            add_edge_func(foothold_idx, user_on_ws, EdgeType.HAS_SESSION)
        path.append(user_on_ws)

        # Step 2: Exploitation of Pivot Server
        pivot_server = server_indices[0] if server_indices else foothold_idx
        nodes[pivot_server].is_vulnerable = True
        add_edge_func(user_on_ws, pivot_server, EdgeType.OPEN)
        path.append(pivot_server)

        # Step 3: Admin session on Pivot Server
        srv_admin_user = user_indices[2] if len(user_indices) > 2 else user_on_ws
        add_edge_func(pivot_server, srv_admin_user, EdgeType.HAS_SESSION)
        path.append(srv_admin_user)

        # Step 4: Group Membership
        da_group = group_indices["Domain-Administrators"]
        add_edge_func(srv_admin_user, da_group, EdgeType.MEMBER_OF)
        path.append(da_group)

        # Step 5: DC Admin
        add_edge_func(da_group, target_idx, EdgeType.ADMIN_TO)
        path.append(target_idx)

        return path
