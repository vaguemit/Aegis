"""
Outsider Node and Insider Bridge Domain Schema.
Defines entity types, bridge vectors, telemetry structures, and remediation models
for detecting and mitigating unmanaged external nodes introduced by insider assets.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class OutsiderType(str, Enum):
    """Classification of unmanaged, outsider nodes."""
    ROGUE_WORKSTATION = "Rogue Workstation / BYOD"
    SHADOW_VM = "Shadow Virtual Machine"
    REVERSE_TUNNEL = "Covert Reverse Tunnel (C2 / SOCKS)"
    UNAUTHORIZED_CONTAINER = "Unauthorized Container / Pod"
    DROPBOX_HARDWARE = "Rogue Physical Drop-Box / Pi"
    CONTRACTOR_ENDPOINT = "Unmanaged Contractor Endpoint"


class BridgeMechanism(str, Enum):
    """Method by which an insider node introduced or bridged the outsider node."""
    DUAL_HOMED_NIC = "Dual-Homed Network Interface"
    SOCKS_CHISEL_TUNNEL = "Chisel / Ligolo Reverse SOCKS Proxy"
    SSH_REMOTE_FORWARD = "SSH Remote Port Forwarding"
    SOFT_AP_TETHERING = "WiFi SoftAP / Mobile Tethering"
    CREDENTIAL_DELEGATION = "Leaked Token / Delegation Pivot"
    VMWARE_SHARED_NAT = "VMware Host-Only / NAT Bridge"


class BridgeRemediationAction(str, Enum):
    """Concrete remediation actions to sever an insider-outsider link."""
    QUARANTINE_VNIC = "Hypervisor vNIC Port Isolation"
    KILL_TUNNEL_PROCESS = "Guest OS Process Termination"
    REVOKE_SESSIONS = "Kerberos TGT & Session Revocation"
    HOST_MICROSEGMENTATION = "Host EDR Network Isolation"
    SEVER_BRIDGE_LINK = "Topological Edge Severance"
    CAPTURE_FORENSIC_SNAPSHOT = "Forensic Snapshot & Memory Dump"


@dataclass
class OutsiderNode:
    """Represents an unmanaged outsider entity introduced into the graph."""
    node_id: str
    name: str
    outsider_type: OutsiderType
    ip_address: str
    mac_address: str
    introduced_by_node_id: int
    introduced_by_node_name: str
    detection_timestamp: float = field(default_factory=time.time)
    has_edr_agent: bool = False
    is_domain_joined: bool = False
    risk_score: float = 0.85
    open_ports: List[int] = field(default_factory=lambda: [22, 1080, 8080])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InsiderBridge:
    """Represents the anomalous connection between an insider node and an outsider node."""
    bridge_id: str
    insider_node_idx: int
    outsider_node_idx: int
    insider_name: str
    outsider_name: str
    mechanism: BridgeMechanism
    protocol: str = "TCP/SOCKS5"
    port: int = 1080
    bytes_transferred: int = 0
    is_active: bool = True
    severity: str = "CRITICAL"
    mitre_techniques: List[str] = field(default_factory=lambda: ["T1090", "T1572", "T1200"])
    introduced_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationPlan:
    """Comprehensive automated remediation plan for an insider-outsider bridge."""
    plan_id: str
    bridge_id: str
    insider_name: str
    outsider_name: str
    actions: List[BridgeRemediationAction]
    baseline_risk: float
    remediated_risk: float
    delta_risk_percent: float
    mitre_mitigations: List[str]
    audit_log: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
