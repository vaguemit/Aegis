"""
Virtual Machine (VM) Infrastructure and Hypervisor Telemetry Simulation Engine.
Models physical host hypervisors (ESXi, Proxmox, Hyper-V), virtual machines,
vSwitches, virtual network interfaces (vNICs), running services, and live VM telemetry streams.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import random
import time


class VMState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    COMPROMISED = "COMPROMISED"
    ISOLATED = "ISOLATED"
    PATCHING = "PATCHING"


class HypervisorType(str, Enum):
    VMWARE_ESXI = "VMware ESXi 8.0"
    PROXMOX_VE = "Proxmox VE 8.1"
    HYPER_V = "Microsoft Hyper-V Server 2022"
    KVM_OPENSTACK = "KVM / OpenStack"


@dataclass
class VirtualNetworkAdapter:
    """Virtual Network Interface Card (vNIC) attached to a VM."""
    interface_name: str
    mac_address: str
    ip_address: str
    subnet: str
    vlan_id: int
    is_promiscuous: bool = False
    rx_bytes: int = 0
    tx_bytes: int = 0


@dataclass
class VirtualMachineInstance:
    """A virtual machine running within the enterprise hypervisor cluster."""
    vm_id: str
    vm_name: str
    node_index: int
    hostname: str
    os_name: str
    cpu_cores: int
    ram_gb: int
    disk_gb: int
    hypervisor_host: str
    vswitch: str
    state: VMState
    network_adapters: List[VirtualNetworkAdapter]
    running_services: List[str]
    open_ports: List[int]
    installed_patches: List[str]
    active_cves: List[str]
    privilege_level: str
    is_domain_controller: bool = False
    is_crown_jewel: bool = False
    active_sessions: List[str] = field(default_factory=list)
    recent_syslog_entries: List[str] = field(default_factory=list)


@dataclass
class HypervisorHost:
    """Physical bare-metal host running hypervisor virtualization software."""
    host_id: str
    host_name: str
    hypervisor_type: HypervisorType
    total_cpu_cores: int
    total_ram_gb: int
    management_ip: str
    hosted_vm_ids: List[str] = field(default_factory=list)


class EnterpriseVMSimulator:
    """
    Simulates enterprise virtual machine infrastructure corresponding to graph topology nodes.
    Generates realistic VM hardware profiles, virtual switches, network routing, and live telemetry.
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.hypervisors: Dict[str, HypervisorHost] = {}
        self.virtual_machines: Dict[str, VirtualMachineInstance] = {}
        self._init_hypervisor_cluster()

    def _init_hypervisor_cluster(self):
        """Initializes cluster of physical hypervisors."""
        hosts = [
            HypervisorHost(
                host_id="esx-cluster-01",
                host_name="BMS-ESXI-CORE-01.corp.internal",
                hypervisor_type=HypervisorType.VMWARE_ESXI,
                total_cpu_cores=64,
                total_ram_gb=512,
                management_ip="10.0.0.11",
            ),
            HypervisorHost(
                host_id="esx-cluster-02",
                host_name="BMS-ESXI-CORE-02.corp.internal",
                hypervisor_type=HypervisorType.VMWARE_ESXI,
                total_cpu_cores=64,
                total_ram_gb=512,
                management_ip="10.0.0.12",
            ),
            HypervisorHost(
                host_id="proxmox-dmz-01",
                host_name="PVE-DMZ-NODE-01.corp.internal",
                hypervisor_type=HypervisorType.PROXMOX_VE,
                total_cpu_cores=32,
                total_ram_gb=256,
                management_ip="172.16.0.5",
            ),
        ]
        for h in hosts:
            self.hypervisors[h.host_id] = h

    def build_vms_from_graph(self, graph_data: Any) -> List[VirtualMachineInstance]:
        """Maps graph nodes into virtual machine instances with realistic system attributes."""
        self.virtual_machines.clear()
        vms = []
        host_keys = list(self.hypervisors.keys())

        for idx in range(graph_data.num_nodes):
            name = graph_data.node_names[idx] if graph_data.node_names and idx < len(graph_data.node_names) else f"node_{idx}"
            is_dc = "dc" in name.lower() or "domain" in name.lower()
            is_server = "server" in name.lower() or "srv" in name.lower() or is_dc
            is_compromised = (idx == graph_data.source_idx)
            is_target = (idx == graph_data.target_idx)

            assigned_host = self.rng.choice(host_keys)

            # Subnet assignment
            if is_dc:
                subnet = "10.0.10.0/24"
                ip = f"10.0.10.{self.rng.randint(10, 20)}"
                vlan = 100
                vswitch = "vSwitch-AD-Core"
            elif is_server:
                subnet = "10.0.20.0/24"
                ip = f"10.0.20.{self.rng.randint(21, 99)}"
                vlan = 200
                vswitch = "vSwitch-Production-Servers"
            else:
                subnet = "10.0.50.0/24"
                ip = f"10.0.50.{self.rng.randint(100, 240)}"
                vlan = 500
                vswitch = "vSwitch-Workstations"

            mac = f"00:50:56:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}"

            adapter = VirtualNetworkAdapter(
                interface_name="eth0",
                mac_address=mac,
                ip_address=ip,
                subnet=subnet,
                vlan_id=vlan,
            )

            # Open ports and services
            ports = [135, 445] # RPC / SMB default for Windows AD
            services = ["LanmanServer", "RpcSs"]
            if is_server:
                ports.extend([3389, 5985, 443])
                services.extend(["TermService", "WinRM", "W3SVC"])
            if is_dc:
                ports.extend([88, 389, 636, 53])
                services.extend(["KDC", "NTDS", "DNS"])

            # Active CVE assignment
            cves = []
            if graph_data.x_matrix[idx, 9] > 0.5: # is_vulnerable
                cve_pool = ["CVE-2020-1472 (ZeroLogon)", "CVE-2021-34527 (PrintNightmare)", "CVE-2022-26923 (Active Directory PrivEsc)", "CVE-2017-0144 (EternalBlue)"]
                cves.append(self.rng.choice(cve_pool))

            vm_inst = VirtualMachineInstance(
                vm_id=f"vm-{idx:03d}",
                vm_name=f"VM-{name.upper()}",
                node_index=idx,
                hostname=f"{name.lower()}.corp.internal",
                os_name="Windows Server 2022 Datacenter" if is_server else "Windows 11 Enterprise 23H2",
                cpu_cores=8 if is_dc else (4 if is_server else 2),
                ram_gb=32 if is_dc else (16 if is_server else 8),
                disk_gb=500 if is_server else 120,
                hypervisor_host=assigned_host,
                vswitch=vswitch,
                state=VMState.COMPROMISED if is_compromised else VMState.RUNNING,
                network_adapters=[adapter],
                running_services=services,
                open_ports=ports,
                installed_patches=["KB5034441", "KB5034123"],
                active_cves=cves,
                privilege_level="SYSTEM" if is_dc else ("Local Administrator" if is_server else "Domain User"),
                is_domain_controller=is_dc,
                is_crown_jewel=is_target,
                active_sessions=["CORP\\Admin" if is_dc else f"CORP\\user_{idx}"],
                recent_syslog_entries=[
                    f"[{time.strftime('%H:%M:%S')}] EventID 4624: An account was successfully logged on (Substatus: 0x0)",
                    f"[{time.strftime('%H:%M:%S')}] EventID 4672: Special privileges assigned to new logon",
                ],
            )
            self.virtual_machines[vm_inst.vm_id] = vm_inst
            self.hypervisors[assigned_host].hosted_vm_ids.append(vm_inst.vm_id)
            vms.append(vm_inst)

        return vms

    def generate_live_telemetry_event(
        self,
        source_vm_id: str,
        target_vm_id: str,
        attack_stage: str,
        protocol: str,
    ) -> Dict[str, Any]:
        """Generates realistic live Event Log / Syslog telemetry for an attack pivot."""
        src_vm = self.virtual_machines.get(source_vm_id)
        dst_vm = self.virtual_machines.get(target_vm_id)

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        src_ip = src_vm.network_adapters[0].ip_address if src_vm else "10.0.50.45"
        dst_ip = dst_vm.network_adapters[0].ip_address if dst_vm else "10.0.10.15"

        event = {
            "timestamp": timestamp,
            "source_vm": src_vm.vm_name if src_vm else source_vm_id,
            "target_vm": dst_vm.vm_name if dst_vm else target_vm_id,
            "source_ip": src_ip,
            "target_ip": dst_ip,
            "attack_stage": attack_stage,
            "protocol": protocol,
            "event_id": 4624 if protocol == "SMB" else (4672 if protocol == "RPC" else 4768),
            "event_type": "Security Audit: Lateral Movement Authentication",
            "log_level": "WARNING" if attack_stage == "Lateral Movement" else "CRITICAL",
            "syslog_message": f"Adversary authenticated from {src_ip} ({src_vm.vm_name if src_vm else 'SRC'}) to {dst_ip} ({dst_vm.vm_name if dst_vm else 'DST'}) via {protocol}. Process: ntdsutil.exe / powershell.exe",
        }
        return event
