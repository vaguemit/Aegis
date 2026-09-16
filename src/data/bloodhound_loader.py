"""
BloodHound & SharpHound Active Directory Graph Ingestor.
Parses real-world Active Directory JSON exports (computers.json, users.json,
groups.json, domains.json, ous.json, or BloodHound CE exports) into AegisPath
tensors (X in R^{N x 20}, multi-relational adjacency tensor A in R^{N x N x 16})
for live GAT inference, attack path discovery, and outsider bridge defense.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import json
import logging
from pathlib import Path
import torch

from src.data.schema import (
    NetworkGraphData,
    EntityType,
    OperatingSystem,
    SecurityProperty,
    EdgeType,
    EDGE_TO_IDX,
    PROPERTY_TO_IDX,
    ENTITY_TO_IDX,
    OS_TO_IDX,
)

logger = logging.getLogger("aegispath.data.bloodhound")

# Mapping BloodHound string relations to AegisPath EdgeType
BH_EDGE_MAP: Dict[str, EdgeType] = {
    "MemberOf": EdgeType.MEMBER_OF,
    "AdminTo": EdgeType.ADMIN_TO,
    "HasSession": EdgeType.HAS_SESSION,
    "CanRDP": EdgeType.CAN_RDP,
    "ExecuteDCOM": EdgeType.EXECUTE_DCOM,
    "AllowedToDelegate": EdgeType.ALLOWED_TO_DELEGATE,
    "WriteDacl": EdgeType.WRITE_DACL,
    "WriteOwner": EdgeType.WRITE_OWNER,
    "GenericAll": EdgeType.GENERIC_ALL,
    "GenericWrite": EdgeType.GENERIC_ALL,
    "AllExtendedRights": EdgeType.GENERIC_ALL,
    "DCSync": EdgeType.DC_SYNC,
    "GetChanges": EdgeType.GET_CHANGES,
    "GetChangesAll": EdgeType.GET_CHANGES_ALL,
    "Contains": EdgeType.CONTAINS,
    "GpLink": EdgeType.GP_LINK,
    "Owns": EdgeType.OWNS,
}


class BloodHoundLoader:
    """
    Ingests raw BloodHound v3/v4/v5 (BloodHound CE) JSON files and transforms
    them into standardized AegisPath NetworkGraphData objects.
    """

    def __init__(self):
        self.node_id_to_idx: Dict[str, int] = {}
        self.node_names: List[str] = []
        self.node_types: List[EntityType] = []
        self.raw_nodes: List[Dict[str, Any]] = []
        self.raw_edges: List[Tuple[str, str, str]] = []  # (src_id, dst_id, relation)

    def load_from_directory(self, dir_path: Union[str, Path]) -> NetworkGraphData:
        """
        Loads all BloodHound JSON files found in a directory.
        Looks for computers.json, users.json, groups.json, domains.json, ous.json.
        """
        p = Path(dir_path)
        if not p.exists():
            raise FileNotFoundError(f"BloodHound directory does not exist: {dir_path}")

        files = list(p.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No JSON files found in directory: {dir_path}")

        for f in files:
            self.load_from_file(f)

        return self.build_graph(scenario_name=f"bloodhound_{p.name}")

    def load_from_file(self, file_path: Union[str, Path]):
        """Parses an individual BloodHound JSON file."""
        p = Path(file_path)
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        self.ingest_json_dict(data)

    def ingest_json_dict(self, data: Dict[str, Any]):
        """
        Ingests parsed BloodHound JSON dictionary.
        Handles both BloodHound Legacy format (with 'data' key) and BloodHound CE format.
        """
        entries = data.get("data", [])
        if not entries and isinstance(data, list):
            entries = data

        for entry in entries:
            props = entry.get("Properties", {})
            entry_type = entry.get("type", "").lower()
            name = props.get("name", props.get("distinguishedname", entry.get("ObjectIdentifier", "")))
            if not name:
                continue

            # Resolve EntityType
            e_type = EntityType.COMPUTER
            if "user" in entry_type or "users" in str(entry.get("ObjectIdentifier", "")).lower():
                e_type = EntityType.USER
            elif "group" in entry_type or "groups" in str(entry.get("ObjectIdentifier", "")).lower():
                e_type = EntityType.GROUP
            elif "computer" in entry_type:
                e_type = EntityType.COMPUTER
            elif "domain" in entry_type:
                e_type = EntityType.DOMAIN
            elif "ou" in entry_type:
                e_type = EntityType.OU
            elif "gpo" in entry_type:
                e_type = EntityType.GPO
            else:
                # Infer from name
                if "$" in name:
                    e_type = EntityType.COMPUTER
                elif "DC=" in name.upper():
                    e_type = EntityType.DOMAIN
                elif "OU=" in name.upper():
                    e_type = EntityType.OU
                else:
                    e_type = EntityType.USER

            node_id = entry.get("ObjectIdentifier", name)
            if node_id not in self.node_id_to_idx:
                idx = len(self.node_names)
                self.node_id_to_idx[node_id] = idx
                self.node_id_to_idx[name] = idx  # Also map by display name
                self.node_names.append(name)
                self.node_types.append(e_type)
                self.raw_nodes.append({
                    "id": node_id,
                    "name": name,
                    "type": e_type,
                    "props": props,
                })

            # Parse Relations / Outbound edges
            # Common BH v4 structure: "Aces": [...], "HasSession": [...], "AllowedToDelegate": [...]
            for rel_name in ["MemberOf", "AdminTo", "HasSession", "CanRDP", "AllowedToDelegate"]:
                for target in entry.get(rel_name, []):
                    target_id = target if isinstance(target, str) else target.get("ObjectIdentifier", target.get("name", ""))
                    if target_id:
                        self.raw_edges.append((node_id, target_id, rel_name))

            for ace in entry.get("Aces", []):
                right = ace.get("RightName", "")
                principal = ace.get("PrincipalSID", ace.get("Principal", ""))
                if right and principal:
                    self.raw_edges.append((principal, node_id, right))

    def build_graph(
        self,
        scenario_name: str = "bloodhound_ingested",
        target_name: Optional[str] = None,
        foothold_name: Optional[str] = None,
    ) -> NetworkGraphData:
        """
        Builds the final NetworkGraphData PyTorch Geometric structure.
        """
        N = len(self.node_names)
        if N == 0:
            raise ValueError("No valid Active Directory nodes ingested.")

        X = torch.zeros((N, 20), dtype=torch.float32)
        A = torch.zeros((N, N, 16), dtype=torch.float32)

        # 1. Populate Node Features
        for idx, node_info in enumerate(self.raw_nodes):
            props = node_info["props"]
            e_type = node_info["type"]
            name = node_info["name"]

            # Entity Type one-hot (Indices 0..5)
            e_idx = ENTITY_TO_IDX.get(e_type, 0)
            X[idx, e_idx] = 1.0

            # Security Properties (Indices 6..11)
            enabled = props.get("enabled", True)
            has_spn = props.get("hasspn", bool(props.get("serviceprincipalnames", [])))
            high_value = props.get("highvalue", False)
            admin_count = props.get("admincount", 0)
            if admin_count > 0 or "domain admin" in name.lower() or "enterprise admin" in name.lower():
                high_value = True

            X[idx, PROPERTY_TO_IDX[SecurityProperty.ENABLED]] = 1.0 if enabled else 0.0
            X[idx, PROPERTY_TO_IDX[SecurityProperty.HAS_SPN]] = 1.0 if has_spn else 0.0
            X[idx, PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]] = 1.0 if high_value else 0.0

            # Operating System (Indices 12..19)
            os_str = props.get("operatingsystem", "").lower()
            if "2016" in os_str or "2019" in os_str or "2022" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_SERVER_2016_2019]] = 1.0
            elif "2012" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_SERVER_2012]] = 1.0
            elif "2008" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_SERVER_2008]] = 1.0
            elif "10" in os_str or "11" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_10]] = 1.0
            elif "7" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_7]] = 1.0
            elif "linux" in os_str or "ubuntu" in os_str or "debian" in os_str:
                X[idx, OS_TO_IDX[OperatingSystem.OTHER_LINUX]] = 1.0
            else:
                X[idx, OS_TO_IDX[OperatingSystem.WIN_10]] = 1.0

        # Designate Foothold (Owned) and Target (Crown Jewel)
        target_idx = None
        foothold_idx = None

        if target_name and target_name in self.node_id_to_idx:
            target_idx = self.node_id_to_idx[target_name]
        if foothold_name and foothold_name in self.node_id_to_idx:
            foothold_idx = self.node_id_to_idx[foothold_name]

        # Automatic fallback target: Domain Admins group or Domain Controller
        if target_idx is None:
            for i, name in enumerate(self.node_names):
                if "domain admins" in name.lower() or "enterprise admins" in name.lower():
                    target_idx = i
                    break
        if target_idx is None and N > 0:
            target_idx = 0

        # Automatic fallback foothold: standard workstation user or lowest-privileged computer
        if foothold_idx is None:
            for i, node_info in enumerate(self.raw_nodes):
                if node_info["type"] in (EntityType.USER, EntityType.COMPUTER) and i != target_idx:
                    foothold_idx = i
                    break
        if foothold_idx is None:
            foothold_idx = min(1, N - 1)

        X[target_idx, PROPERTY_TO_IDX[SecurityProperty.TARGET]] = 1.0
        X[foothold_idx, PROPERTY_TO_IDX[SecurityProperty.OWNED]] = 1.0

        # 2. Populate Multi-Relational Adjacency Tensor
        edge_count = 0
        for src_id, dst_id, rel_name in self.raw_edges:
            src_u = self.node_id_to_idx.get(src_id)
            dst_v = self.node_id_to_idx.get(dst_id)
            if src_u is not None and dst_v is not None and src_u < N and dst_v < N:
                mapped_edge = BH_EDGE_MAP.get(rel_name, EdgeType.MEMBER_OF)
                ch = EDGE_TO_IDX[mapped_edge]
                A[src_u, dst_v, ch] = 1.0
                edge_count += 1

        # Ground truth attack path matrix Y (can be populated by shortest path or GAT)
        Y = torch.zeros((N, N), dtype=torch.float32)

        return NetworkGraphData(
            graph_id=f"bh_{abs(hash(scenario_name)) % 1000000:06d}",
            num_nodes=N,
            x_matrix=X,
            adj_tensor=A,
            y_matrix=Y,
            node_names=self.node_names,
            source_idx=foothold_idx,
            target_idx=target_idx,
        )


def create_realistic_enterprise_ad_sample() -> NetworkGraphData:
    """
    Generates a realistic multi-tier Active Directory security graph matching
    real SharpHound outputs (Tier-0 Domain Admins, Domain Controllers, File Shares,
    Kerberoastable service accounts, and workstation users).
    """
    loader = BloodHoundLoader()

    sample_nodes = [
        # Domain Controller & Admins (Tier 0)
        {"type": "computer", "ObjectIdentifier": "S-1-5-21-DC01", "Properties": {"name": "DC01.CORP.LOCAL", "highvalue": True, "operatingsystem": "Windows Server 2022 Standard", "enabled": True}},
        {"type": "group", "ObjectIdentifier": "S-1-5-21-512", "Properties": {"name": "DOMAIN ADMINS@CORP.LOCAL", "highvalue": True, "admincount": 1}},
        {"type": "group", "ObjectIdentifier": "S-1-5-21-519", "Properties": {"name": "ENTERPRISE ADMINS@CORP.LOCAL", "highvalue": True, "admincount": 1}},
        {"type": "user", "ObjectIdentifier": "S-1-5-21-DA-USER", "Properties": {"name": "DA_ADMINISTRATOR@CORP.LOCAL", "highvalue": True, "admincount": 1}},

        # Servers & Tier 1 Services
        {"type": "computer", "ObjectIdentifier": "S-1-5-21-FS01", "Properties": {"name": "FILESERVER01.CORP.LOCAL", "operatingsystem": "Windows Server 2019 Datacenter", "highvalue": False}},
        {"type": "computer", "ObjectIdentifier": "S-1-5-21-SQL01", "Properties": {"name": "SQL-PROD01.CORP.LOCAL", "operatingsystem": "Windows Server 2016 Standard", "highvalue": False}},
        {"type": "user", "ObjectIdentifier": "S-1-5-21-SQL-SVC", "Properties": {"name": "SVC_SQLSERVICE@CORP.LOCAL", "hasspn": True, "highvalue": False}},
        {"type": "group", "ObjectIdentifier": "S-1-5-21-SERVER-ADMINS", "Properties": {"name": "SERVER ADMINS@CORP.LOCAL", "highvalue": False}},

        # Tier 2 Workstations & Employees (Foothold)
        {"type": "computer", "ObjectIdentifier": "S-1-5-21-WS01", "Properties": {"name": "WS-FINANCE-01.CORP.LOCAL", "operatingsystem": "Windows 10 Enterprise", "highvalue": False}},
        {"type": "computer", "ObjectIdentifier": "S-1-5-21-WS02", "Properties": {"name": "WS-ENGINEERING-02.CORP.LOCAL", "operatingsystem": "Windows 11 Enterprise", "highvalue": False}},
        {"type": "user", "ObjectIdentifier": "S-1-5-21-USER-JDOE", "Properties": {"name": "JDOE@CORP.LOCAL", "highvalue": False}},
        {"type": "user", "ObjectIdentifier": "S-1-5-21-USER-ASMITH", "Properties": {"name": "ASMITH@CORP.LOCAL", "highvalue": False}},
        {"type": "group", "ObjectIdentifier": "S-1-5-21-ALL-USERS", "Properties": {"name": "DOMAIN USERS@CORP.LOCAL", "highvalue": False}},

        # Active Directory Organizational Units
        {"type": "ou", "ObjectIdentifier": "OU=Workstations,DC=corp,DC=local", "Properties": {"name": "OU=WORKSTATIONS,DC=CORP,DC=LOCAL"}},
        {"type": "ou", "ObjectIdentifier": "OU=Servers,DC=corp,DC=local", "Properties": {"name": "OU=SERVERS,DC=CORP,DC=LOCAL"}},
        {"type": "domain", "ObjectIdentifier": "DC=corp,DC=local", "Properties": {"name": "CORP.LOCAL", "highvalue": True}},
    ]

    # Explicit attack chain:
    # 1. Foothold WS-FINANCE-01 (node 8) can RDP to SQL-PROD01 (node 5)
    sample_nodes[8]["CanRDP"] = ["S-1-5-21-SQL01"]
    # 2. SQL-PROD01 (node 5) has active session for DA_ADMINISTRATOR (node 3) [LSASS dump]
    sample_nodes[5]["HasSession"] = ["S-1-5-21-DA-USER"]
    # 3. DA_ADMINISTRATOR (node 3) is MemberOf DOMAIN ADMINS (node 1)
    sample_nodes[3]["MemberOf"] = ["S-1-5-21-512"]
    # 4. DOMAIN ADMINS (node 1) is AdminTo DC01 (node 0)
    sample_nodes[1]["AdminTo"] = ["S-1-5-21-DC01"]

    # Auxiliary enterprise relationships
    sample_nodes[10]["HasSession"] = ["S-1-5-21-WS01"]
    sample_nodes[10]["MemberOf"] = ["S-1-5-21-ALL-USERS"]
    sample_nodes[7]["AdminTo"] = ["S-1-5-21-SQL01", "S-1-5-21-FS01"]

    loader.ingest_json_dict({"data": sample_nodes})
    g = loader.build_graph(
        scenario_name="corp_ad_production_bloodhound",
        target_name="DOMAIN ADMINS@CORP.LOCAL",
        foothold_name="WS-FINANCE-01.CORP.LOCAL",
    )

    # Set ground truth path in Y matrix: 8 -> 5 -> 3 -> 1
    u_ws = loader.node_id_to_idx["S-1-5-21-WS01"]
    u_sql = loader.node_id_to_idx["S-1-5-21-SQL01"]
    u_da = loader.node_id_to_idx["S-1-5-21-DA-USER"]
    u_target = loader.node_id_to_idx["S-1-5-21-512"]

    g.y_matrix[u_ws, u_sql] = 1.0
    g.y_matrix[u_sql, u_da] = 1.0
    g.y_matrix[u_da, u_target] = 1.0
    g.attack_path_nodes = [u_ws, u_sql, u_da, u_target]

    return g
