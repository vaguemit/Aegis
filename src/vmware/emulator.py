"""
High-Fidelity VMware Hypervisor and vCenter Emulation Provider.
Generates realistic enterprise ESXi clusters, virtual machines, and vSwitch networks
for testing and production dry-run scenarios without requiring physical hypervisor hardware.
"""

from typing import List, Dict, Any
import random
import time

from src.vmware.models import (
    VMwareHostInfo,
    VMwareVMInfo,
    VMwareNICInfo,
    VMwareVSwitchInfo,
    VMwarePortGroupInfo,
    PowerState,
    VMwareDiscoveryReport,
)


class VMwareClusterEmulator:
    """
    Simulates physical and virtual infrastructure of an enterprise VMware vSphere environment.
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate_cluster(self, num_vms: int = 8) -> VMwareDiscoveryReport:
        """Generates a complete simulated VMware cluster inventory."""
        hosts = [
            VMwareHostInfo(
                host_id="host-101",
                name="esxi-node-01.corp.internal",
                cluster="Cluster-Production",
                esxi_version="VMware ESXi 8.0.2 build-22380479",
                management_ip="10.0.0.11",
                total_cpu_mhz=64 * 2400,
                total_memory_mb=512 * 1024,
                vm_ids=[],
                state="CONNECTED",
            ),
            VMwareHostInfo(
                host_id="host-102",
                name="esxi-node-02.corp.internal",
                cluster="Cluster-Production",
                esxi_version="VMware ESXi 8.0.2 build-22380479",
                management_ip="10.0.0.12",
                total_cpu_mhz=64 * 2400,
                total_memory_mb=512 * 1024,
                vm_ids=[],
                state="CONNECTED",
            ),
        ]

        portgroups = [
            VMwarePortGroupInfo(name="AD-Core-VLAN100", vswitch="vSwitch0", vlan_id=100),
            VMwarePortGroupInfo(name="Prod-VLAN200", vswitch="vSwitch0", vlan_id=200),
            VMwarePortGroupInfo(name="Workstations-VLAN500", vswitch="vSwitch0", vlan_id=500),
            VMwarePortGroupInfo(name="DMZ-VLAN50", vswitch="vSwitch1", vlan_id=50, promiscuous_mode=False),
            VMwarePortGroupInfo(name="Quarantine_VLAN_999", vswitch="vSwitch0", vlan_id=999),
        ]

        vswitches = [
            VMwareVSwitchInfo(
                name="vSwitch0",
                switch_type="Standard",
                num_ports=128,
                portgroups=[p for p in portgroups if p.vswitch == "vSwitch0"],
                uplinks=["vmnic0", "vmnic1"],
            ),
            VMwareVSwitchInfo(
                name="vSwitch1",
                switch_type="Standard",
                num_ports=64,
                portgroups=[p for p in portgroups if p.vswitch == "vSwitch1"],
                uplinks=["vmnic2"],
            ),
        ]

        vm_templates = [
            ("VM-DC01", "Windows Server 2022 Datacenter", 8, 32768, "10.0.10.15", "AD-Core-VLAN100", 100, False),
            ("VM-DC02", "Windows Server 2022 Datacenter", 8, 32768, "10.0.10.16", "AD-Core-VLAN100", 100, False),
            ("VM-FILE01", "Windows Server 2019 Standard", 4, 16384, "10.0.20.25", "Prod-VLAN200", 200, False),
            ("VM-SQL01", "Windows Server 2022 Datacenter", 8, 65536, "10.0.20.30", "Prod-VLAN200", 200, False),
            ("VM-WEB01", "Ubuntu 22.04 LTS", 4, 8192, "172.16.0.45", "DMZ-VLAN50", 50, False),
            ("VM-WS01", "Windows 11 Enterprise 23H2", 2, 8192, "10.0.50.101", "Workstations-VLAN500", 500, False),
            ("VM-WS02", "Windows 11 Enterprise 23H2", 2, 8192, "10.0.50.102", "Workstations-VLAN500", 500, False),
            ("VM-ROGUE-SHADOW", "Kali Linux 2024.1", 4, 4096, "192.168.254.88", "Workstations-VLAN500", 500, True),
        ]

        vms: List[VMwareVMInfo] = []
        for idx, (name, os_name, cpu, ram, ip, pg_name, vlan, is_rogue) in enumerate(vm_templates[:num_vms]):
            host = hosts[idx % len(hosts)]
            mac = f"00:50:56:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}:{self.rng.randint(10,99):02x}"
            
            nic = VMwareNICInfo(
                label="Network adapter 1",
                mac_address=mac,
                ip_addresses=[ip],
                portgroup=pg_name,
                vswitch="vSwitch0" if vlan != 50 else "vSwitch1",
                vlan_id=vlan,
                is_connected=True,
                is_promiscuous=is_rogue,
            )

            vm = VMwareVMInfo(
                vm_id=f"vm-{idx + 200}",
                name=name,
                power_state=PowerState.POWERED_ON,
                guest_os=os_name,
                host_id=host.host_id,
                cpu_count=cpu,
                memory_mb=ram,
                ip_address=ip,
                nics=[nic],
                is_template=False,
                is_domain_joined=not is_rogue,
                is_outsider=is_rogue,
                is_isolated=False,
                tags=["production" if not is_rogue else "unauthorized", "aegispath-managed"],
            )
            vms.append(vm)
            host.vm_ids.append(vm.vm_id)

        return VMwareDiscoveryReport(
            cluster_name="Cluster-Production",
            vcenter_host="vcenter.corp.internal",
            total_hosts=len(hosts),
            total_vms=len(vms),
            total_vswitches=len(vswitches),
            hosts=hosts,
            vms=vms,
            vswitches=vswitches,
            discovered_at=time.time(),
        )
