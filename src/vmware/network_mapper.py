"""
VMware vSwitch and PortGroup Network Topology Mapper.
Maps virtual networking infrastructure, portgroups, VLAN tag distributions,
and audits promiscuous mode security policies.
"""

from typing import Dict, List, Optional, Any
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import VMwareVSwitchInfo, VMwarePortGroupInfo, VMwareVMInfo
from src.vmware.discovery import VMwareTopologyDiscoverer

logger = logging.getLogger("aegispath.vmware.network_mapper")


class VMwareNetworkMapper:
    """
    Analyzes virtual switch topologies, portgroup assignments, and network isolation policies.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)

    def get_network_topology(self) -> Dict[str, Any]:
        """Maps complete vSwitch network topology with connected VMs and VLANs."""
        report = self.discoverer.discover_cluster()
        
        topology: Dict[str, Any] = {
            "vswitches": [],
            "portgroups": {},
            "vlan_distribution": {},
            "policy_warnings": [],
        }

        for sw in report.vswitches:
            sw_data = {
                "name": sw.name,
                "type": sw.switch_type,
                "ports": sw.num_ports,
                "uplinks": sw.uplinks,
                "portgroups": [pg.name for pg in sw.portgroups],
            }
            topology["vswitches"].append(sw_data)

            for pg in sw.portgroups:
                # Count VMs in this portgroup
                vms_in_pg = []
                for vm in report.vms:
                    for nic in vm.nics:
                        if nic.portgroup == pg.name:
                            vms_in_pg.append(vm.name)

                pg.active_vm_count = len(vms_in_pg)
                topology["portgroups"][pg.name] = {
                    "vswitch": pg.vswitch,
                    "vlan_id": pg.vlan_id,
                    "vm_count": len(vms_in_pg),
                    "connected_vms": vms_in_pg,
                    "promiscuous": pg.promiscuous_mode,
                }

                # Track VLAN distribution
                vlan_key = f"VLAN_{pg.vlan_id}"
                if vlan_key not in topology["vlan_distribution"]:
                    topology["vlan_distribution"][vlan_key] = []
                topology["vlan_distribution"][vlan_key].extend(vms_in_pg)

                # Audit security policy
                if pg.promiscuous_mode:
                    topology["policy_warnings"].append({
                        "portgroup": pg.name,
                        "vswitch": pg.vswitch,
                        "issue": "PROMISCUOUS_MODE_ENABLED",
                        "severity": "CRITICAL",
                        "description": f"Portgroup '{pg.name}' allows promiscuous mode packet sniffing.",
                    })

        return topology
