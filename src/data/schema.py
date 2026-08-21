"""
Enterprise Network and Attack Path Schema Definitions.
Defines entity categories, edge relationships, operating systems, security flags,
and structured graph data containers for AegisPath.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import torch


class EntityType(str, Enum):
    """Active Directory / Enterprise Entity Types (Indices 0..5 in feature vector)."""
    COMPUTER = "Computer"
    OU = "OU"
    USER = "User"
    GROUP = "Group"
    GPO = "GPO"
    DOMAIN = "Domain"


class SecurityProperty(str, Enum):
    """Boolean security and attack state flags (Indices 6..11 in feature vector)."""
    ENABLED = "enabled"
    HAS_SPN = "hasspn"              # Kerberoastable Service Principal Name
    HIGH_VALUE = "highvalue"        # Tier-0 / Critical Asset (Domain Controller, Admin)
    IS_VULNERABLE = "is_vulnerable" # Known CVE / Exploit path available
    TARGET = "target"               # End goal of the attack path (Crown Jewel)
    OWNED = "owned"                 # Attacker initial foothold (Compromised source node)


class OperatingSystem(str, Enum):
    """Operating System Categories (Indices 12..19 in feature vector)."""
    WIN_SERVER_2003 = "Windows Server 2003"
    WIN_SERVER_2008 = "Windows Server 2008"
    WIN_7 = "Windows 7"
    WIN_10 = "Windows 10"
    WIN_XP = "Windows XP"
    WIN_SERVER_2012 = "Windows Server 2012"
    WIN_SERVER_2016_2019 = "Windows Server 2016/2019"
    OTHER_LINUX = "Other/Linux"


class EdgeType(str, Enum):
    """16 Directed Enterprise & Active Directory Edge Relationships (Channels 0..15)."""
    ADMIN_TO = "AdminTo"
    ALLOWED_TO_DELEGATE = "AllowedToDelegate"
    CAN_RDP = "CanRDP"
    CONTAINS = "Contains"
    DC_SYNC = "DCSync"
    EXECUTE_DCOM = "ExecuteDCOM"
    GENERIC_ALL = "GenericAll"
    GET_CHANGES = "GetChanges"
    GET_CHANGES_ALL = "GetChangesAll"
    GP_LINK = "GpLink"
    HAS_SESSION = "HasSession"
    MEMBER_OF = "MemberOf"
    OPEN = "Open"
    OWNS = "Owns"
    WRITE_DACL = "WriteDacl"
    WRITE_OWNER = "WriteOwner"


# Standardized Feature Layout Constants
ENTITY_TYPES: List[EntityType] = [
    EntityType.COMPUTER,
    EntityType.OU,
    EntityType.USER,
    EntityType.GROUP,
    EntityType.GPO,
    EntityType.DOMAIN,
]

SECURITY_PROPERTIES: List[SecurityProperty] = [
    SecurityProperty.ENABLED,
    SecurityProperty.HAS_SPN,
    SecurityProperty.HIGH_VALUE,
    SecurityProperty.IS_VULNERABLE,
    SecurityProperty.TARGET,
    SecurityProperty.OWNED,
]

OPERATING_SYSTEMS: List[OperatingSystem] = [
    OperatingSystem.WIN_SERVER_2003,
    OperatingSystem.WIN_SERVER_2008,
    OperatingSystem.WIN_7,
    OperatingSystem.WIN_10,
    OperatingSystem.WIN_XP,
    OperatingSystem.WIN_SERVER_2012,
    OperatingSystem.WIN_SERVER_2016_2019,
    OperatingSystem.OTHER_LINUX,
]

EDGE_TYPES: List[EdgeType] = [
    EdgeType.ADMIN_TO,
    EdgeType.ALLOWED_TO_DELEGATE,
    EdgeType.CAN_RDP,
    EdgeType.CONTAINS,
    EdgeType.DC_SYNC,
    EdgeType.EXECUTE_DCOM,
    EdgeType.GENERIC_ALL,
    EdgeType.GET_CHANGES,
    EdgeType.GET_CHANGES_ALL,
    EdgeType.GP_LINK,
    EdgeType.HAS_SESSION,
    EdgeType.MEMBER_OF,
    EdgeType.OPEN,
    EdgeType.OWNS,
    EdgeType.WRITE_DACL,
    EdgeType.WRITE_OWNER,
]

NUM_NODE_FEATURES: int = len(ENTITY_TYPES) + len(SECURITY_PROPERTIES) + len(OPERATING_SYSTEMS) # 20
NUM_EDGE_TYPES: int = len(EDGE_TYPES) # 16

# Index Lookups
ENTITY_TO_IDX: Dict[EntityType, int] = {e: i for i, e in enumerate(ENTITY_TYPES)}
PROPERTY_TO_IDX: Dict[SecurityProperty, int] = {p: len(ENTITY_TYPES) + i for i, p in enumerate(SECURITY_PROPERTIES)}
OS_TO_IDX: Dict[OperatingSystem, int] = {o: len(ENTITY_TYPES) + len(SECURITY_PROPERTIES) + i for i, o in enumerate(OPERATING_SYSTEMS)}
EDGE_TO_IDX: Dict[EdgeType, int] = {e: i for i, e in enumerate(EDGE_TYPES)}
IDX_TO_EDGE: Dict[int, EdgeType] = {i: e for i, e in enumerate(EDGE_TYPES)}


@dataclass
class NetworkNode:
    """Representation of an individual entity node in an enterprise network."""
    node_id: int
    name: str
    entity_type: EntityType
    os: Optional[OperatingSystem] = None
    is_enabled: bool = True
    has_spn: bool = False
    is_high_value: bool = False
    is_vulnerable: bool = False
    is_target: bool = False
    is_owned: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_feature_vector(self) -> torch.Tensor:
        """Encodes the node into a 20-dimensional feature tensor."""
        vec = torch.zeros(NUM_NODE_FEATURES, dtype=torch.float32)
        # Entity type one-hot (0..5)
        vec[ENTITY_TO_IDX[self.entity_type]] = 1.0
        # Security properties (6..11)
        if self.is_enabled:
            vec[PROPERTY_TO_IDX[SecurityProperty.ENABLED]] = 1.0
        if self.has_spn:
            vec[PROPERTY_TO_IDX[SecurityProperty.HAS_SPN]] = 1.0
        if self.is_high_value:
            vec[PROPERTY_TO_IDX[SecurityProperty.HIGH_VALUE]] = 1.0
        if self.is_vulnerable:
            vec[PROPERTY_TO_IDX[SecurityProperty.IS_VULNERABLE]] = 1.0
        if self.is_target:
            vec[PROPERTY_TO_IDX[SecurityProperty.TARGET]] = 1.0
        if self.is_owned:
            vec[PROPERTY_TO_IDX[SecurityProperty.OWNED]] = 1.0
        # OS one-hot (12..19)
        if self.os is not None and self.os in OS_TO_IDX:
            vec[OS_TO_IDX[self.os]] = 1.0
        return vec


@dataclass
class NetworkEdge:
    """Directed edge between two network entities."""
    source_idx: int
    target_idx: int
    edge_type: EdgeType
    is_attack_path: bool = False
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkGraphData:
    """Container for a complete enterprise network graph with features and attack labels."""
    graph_id: str
    num_nodes: int
    x_matrix: torch.Tensor             # Shape: (num_nodes, 20)
    adj_tensor: torch.Tensor           # Shape: (num_nodes, num_nodes, 16)
    y_matrix: torch.Tensor             # Shape: (num_nodes, num_nodes)
    node_names: Optional[List[str]] = None
    source_idx: Optional[int] = None
    target_idx: Optional[int] = None
    attack_path_nodes: Optional[List[int]] = None

    def __post_init__(self):
        # Auto-detect source (owned) and target from feature matrix if not explicitly passed
        if self.source_idx is None and self.x_matrix is not None:
            owned_col = PROPERTY_TO_IDX[SecurityProperty.OWNED]
            owned_indices = (self.x_matrix[:, owned_col] > 0.5).nonzero(as_tuple=True)[0]
            if len(owned_indices) > 0:
                self.source_idx = int(owned_indices[0].item())

        if self.target_idx is None and self.x_matrix is not None:
            target_col = PROPERTY_TO_IDX[SecurityProperty.TARGET]
            target_indices = (self.x_matrix[:, target_col] > 0.5).nonzero(as_tuple=True)[0]
            if len(target_indices) > 0:
                self.target_idx = int(target_indices[0].item())

        if self.attack_path_nodes is None and self.y_matrix is not None:
            self.attack_path_nodes = self._extract_path_sequence()

    def _extract_path_sequence(self) -> List[int]:
        """Extracts ordered sequence of node indices from binary attack path matrix Y."""
        if self.source_idx is None or self.y_matrix is None:
            return []
        path = [self.source_idx]
        current = self.source_idx
        visited = {current}
        max_hops = self.num_nodes

        for _ in range(max_hops):
            successors = (self.y_matrix[current] > 0.5).nonzero(as_tuple=True)[0]
            unvisited_succs = [s.item() for s in successors if s.item() not in visited]
            if not unvisited_succs:
                break
            next_node = unvisited_succs[0]
            path.append(next_node)
            visited.add(next_node)
            current = next_node
            if self.target_idx is not None and current == self.target_idx:
                break
        return path
