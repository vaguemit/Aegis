"""
VMware Virtual Machine Manager.
Provides lookup, lifecycle state inspection, guest IP resolution,
and hardware profiling for virtual machines in the vSphere inventory.
"""

from typing import Dict, List, Optional
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import VMwareVMInfo, PowerState
from src.vmware.discovery import VMwareTopologyDiscoverer

logger = logging.getLogger("aegispath.vmware.vm_manager")


class VMwareVMManager:
    """
    Manages VM query, caching, and state retrieval from VMware vCenter.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)
        self._vm_cache: Dict[str, VMwareVMInfo] = {}

    def refresh_vms(self) -> List[VMwareVMInfo]:
        """Refreshes the internal cache of virtual machines."""
        report = self.discoverer.discover_cluster()
        self._vm_cache = {vm.vm_id: vm for vm in report.vms}
        return list(self._vm_cache.values())

    def list_all_vms(self) -> List[VMwareVMInfo]:
        """Returns all virtual machines in the inventory."""
        if not self._vm_cache:
            self.refresh_vms()
        return list(self._vm_cache.values())

    def get_vm_by_id(self, vm_id: str) -> Optional[VMwareVMInfo]:
        """Retrieves a specific VM by its vSphere MOID (Managed Object ID)."""
        if vm_id not in self._vm_cache:
            self.refresh_vms()
        return self._vm_cache.get(vm_id)

    def get_vm_by_name(self, name: str) -> Optional[VMwareVMInfo]:
        """Retrieves a specific VM by its display name."""
        if not self._vm_cache:
            self.refresh_vms()
        for vm in self._vm_cache.values():
            if vm.name.lower() == name.lower():
                return vm
        return None

    def get_powered_on_vms(self) -> List[VMwareVMInfo]:
        """Filters VMs to only those currently powered on."""
        return [vm for vm in self.list_all_vms() if vm.power_state == PowerState.POWERED_ON]
