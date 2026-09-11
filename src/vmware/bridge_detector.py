"""
VMware Dual-Homed NIC and Unauthorized Bridge Detector.
Identifies insider virtual machines bridging protected internal enterprise VLANs
with external DMZ, guest, or unmanaged virtual portgroups.
"""

from typing import Dict, List, Optional, Any
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import VMwareVMInfo
from src.vmware.discovery import VMwareTopologyDiscoverer

logger = logging.getLogger("aegispath.vmware.bridge_detector")


class VMwareBridgeDetector:
    """
    Detects cross-VLAN bridging assets and perimeter leakage across hypervisor portgroups.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)

    def find_bridging_vms(self) -> List[Dict[str, Any]]:
        """
        Scans all VMs to locate endpoints with multiple network adapters connected
        to conflicting network security tiers.
        """
        report = self.discoverer.discover_cluster()
        bridging_vms = []

        for vm in report.vms:
            if len(vm.nics) > 1:
                portgroups_attached = [nic.portgroup for nic in vm.nics]
                vlans_attached = [nic.vlan_id for nic in vm.nics]

                # Check if internal (VLAN 100/200/500) and external/DMZ (VLAN 50/0) are co-located
                has_internal = any(v in (100, 200, 500) for v in vlans_attached)
                has_external = any(v in (50, 0, 99) for v in vlans_attached)

                if has_internal and has_external:
                    finding = {
                        "vm_id": vm.vm_id,
                        "vm_name": vm.name,
                        "ip_address": vm.ip_address,
                        "nic_count": len(vm.nics),
                        "portgroups": portgroups_attached,
                        "vlans": vlans_attached,
                        "threat": "UNAUTHORIZED_CROSS_TIER_BRIDGE",
                        "severity": "CRITICAL",
                        "description": f"VM '{vm.name}' is dual-homed across internal VLANs and external DMZ networks, creating a lateral movement bypass.",
                        "recommended_mitigation": "DISCONNECT_EXTERNAL_VNIC",
                    }
                    bridging_vms.append(finding)

        return bridging_vms
