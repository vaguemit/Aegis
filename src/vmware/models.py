"""
Domain data models for VMware vSphere infrastructure entities,
network topologies, forensic artifacts, and quarantine actions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class PowerState(str, Enum):
    POWERED_ON = "POWERED_ON"
    POWERED_OFF = "POWERED_OFF"
    SUSPENDED = "SUSPENDED"


class QuarantineMethod(str, Enum):
    PORTGROUP_MIGRATION = "PORTGROUP_MIGRATION"       # Move vNIC to isolated VLAN 999
    VNIC_DISCONNECT = "VNIC_DISCONNECT"               # Set vNIC connected = False
    GUEST_MICROSEGMENTATION = "GUEST_MICROSEGMENTATION" # Inject firewall drop rule in guest
    POWER_OFF = "POWER_OFF"                           # Emergency shutdown


@dataclass
class VMwareNICInfo:
    """Virtual Network Adapter (vNIC) metadata."""
    label: str
    mac_address: str
    ip_addresses: List[str]
    portgroup: str
    vswitch: str
    vlan_id: int
    is_connected: bool = True
    is_promiscuous: bool = False
    mac_spoofing_allowed: bool = False


@dataclass
class VMwareVMInfo:
    """Virtual Machine entity metadata from vSphere."""
    vm_id: str
    name: str
    power_state: PowerState
    guest_os: str
    host_id: str
    cpu_count: int
    memory_mb: int
    ip_address: Optional[str]
    nics: List[VMwareNICInfo] = field(default_factory=list)
    is_template: bool = False
    is_domain_joined: bool = True
    is_outsider: bool = False
    is_isolated: bool = False
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class VMwareHostInfo:
    """ESXi bare-metal physical hypervisor host."""
    host_id: str
    name: str
    cluster: str
    esxi_version: str
    management_ip: str
    total_cpu_mhz: int
    total_memory_mb: int
    vm_ids: List[str] = field(default_factory=list)
    state: str = "CONNECTED"


@dataclass
class VMwarePortGroupInfo:
    """vSwitch PortGroup network definition."""
    name: str
    vswitch: str
    vlan_id: int
    promiscuous_mode: bool = False
    mac_changes_allowed: bool = False
    forged_transmits_allowed: bool = False
    active_vm_count: int = 0


@dataclass
class VMwareVSwitchInfo:
    """Standard or Distributed Virtual Switch (vSwitch/DVS)."""
    name: str
    switch_type: str = "Standard"                     # Standard or Distributed
    num_ports: int = 128
    portgroups: List[VMwarePortGroupInfo] = field(default_factory=list)
    uplinks: List[str] = field(default_factory=list)


@dataclass
class VMwareSnapshotInfo:
    """Virtual machine snapshot artifact for digital forensics."""
    snapshot_id: str
    vm_id: str
    vm_name: str
    name: str
    description: str
    timestamp: float = field(default_factory=time.time)
    memory_dump_included: bool = True
    file_path: Optional[str] = None


@dataclass
class VMwareGuestProcess:
    """Process running inside guest OS queried via Guest Operations API."""
    pid: int
    name: str
    cmdline: str
    owner: str
    start_time: str
    is_rogue: bool = False


@dataclass
class VMwareQuarantineResult:
    """Result of an active defense quarantine action."""
    action_id: str
    vm_id: str
    vm_name: str
    method: QuarantineMethod
    success: bool
    details: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class VMwareDiscoveryReport:
    """Full inventory snapshot from VMware vCenter/ESXi cluster."""
    cluster_name: str
    vcenter_host: str
    total_hosts: int
    total_vms: int
    total_vswitches: int
    hosts: List[VMwareHostInfo]
    vms: List[VMwareVMInfo]
    vswitches: List[VMwareVSwitchInfo]
    discovered_at: float = field(default_factory=time.time)
