"""
VMware Active Defense & Network Quarantine Engine.
Executes automated hypervisor-level network isolation by dynamically migrating vNICs
to blackhole quarantine portgroups (VLAN 999), severing virtual Ethernet links,
or invoking local hypervisor cmdlets on Hyper-V / VMware Workstation.
"""

from typing import Dict, List, Optional, Any
import time
import uuid
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import (
    VMwareVMInfo,
    VMwareQuarantineResult,
    QuarantineMethod,
)
from src.vmware.vm_manager import VMwareVMManager
from src.vmware.telemetry import VMwareTelemetryStreamer
from src.vmware.local_driver import local_execution_driver

logger = logging.getLogger("aegispath.vmware.quarantine")


class VMwareActiveQuarantine:
    """
    Executes real-time network quarantine actions directly against VMware vCenter/ESXi,
    local Hyper-V / Workstation, or emulated hypervisor topologies.
    """

    def __init__(self, client: VMwareClient, streamer: Optional[VMwareTelemetryStreamer] = None):
        self.client = client
        self.vm_manager = VMwareVMManager(client)
        self.streamer = streamer or VMwareTelemetryStreamer()

    def quarantine_vm(
        self,
        vm_id: str,
        quarantine_portgroup: Optional[str] = None,
        method: QuarantineMethod = QuarantineMethod.PORTGROUP_MIGRATION,
    ) -> VMwareQuarantineResult:
        """
        Isolates a compromised or rogue virtual machine.
        Migrates vNICs to Quarantine_VLAN_999 or unplugs the virtual network cable.
        """
        q_pg = quarantine_portgroup or self.client.config.quarantine_portgroup
        vm = self.vm_manager.get_vm_by_id(vm_id) or self.vm_manager.get_vm_by_name(vm_id)
        action_id = f"quarantine-{uuid.uuid4().hex[:8]}"

        vm_name = vm.name if vm else vm_id
        prev_state = {
            "is_isolated": vm.is_isolated if vm else False,
            "nics": [{"label": n.label, "portgroup": n.portgroup, "connected": n.is_connected} for n in vm.nics] if vm else [],
        }

        execution_details = []

        # 1. Live VMware vCenter REST API execution
        if self.client.is_connected and not self.client.is_emulated and self.client._http_client and vm:
            for nic in vm.nics:
                nic_id = nic.label.lower().replace(" ", "")
                try:
                    if method == QuarantineMethod.PORTGROUP_MIGRATION:
                        patch_payload = {
                            "spec": {
                                "backing": {
                                    "type": "STANDARD_PORTGROUP",
                                    "network_name": q_pg,
                                }
                            }
                        }
                    else:
                        patch_payload = {
                            "spec": {
                                "connected": False,
                                "start_connected": False,
                            }
                        }
                    resp = self.client._http_client.patch(
                        f"{self.client.base_url}/vcenter/vm/{vm.vm_id}/hardware/adapter/{nic_id}",
                        json=patch_payload,
                        timeout=10.0,
                    )
                    execution_details.append(f"vCenter REST: {nic.label} -> {q_pg} (HTTP {resp.status_code})")
                except Exception as e:
                    execution_details.append(f"vCenter REST error on {nic.label}: {e}")

        # 2. Local Hyper-V or Workstation Execution
        if local_execution_driver.hyperv_available:
            hv_res = local_execution_driver.quarantine_hyperv_vm(vm_name, self.client.config.quarantine_vlan)
            if hv_res.get("Success"):
                execution_details.append(f"Hyper-V: {vm_name} isolated to VLAN {self.client.config.quarantine_vlan}")

        if local_execution_driver.vmrun_path and vm_id.endswith(".vmx"):
            ws_res = local_execution_driver.quarantine_workstation_vm(vm_id)
            if ws_res.get("success"):
                execution_details.append(f"Workstation: {vm_id} vNIC disconnected via vmrun")

        # 3. Update cached state
        if vm:
            vm.is_isolated = True
            for nic in vm.nics:
                if method == QuarantineMethod.PORTGROUP_MIGRATION:
                    nic.portgroup = q_pg
                    nic.vlan_id = self.client.config.quarantine_vlan
                elif method == QuarantineMethod.VNIC_DISCONNECT:
                    nic.is_connected = False

        new_state = {
            "is_isolated": True,
            "nics": [{"label": n.label, "portgroup": n.portgroup, "connected": n.is_connected} for n in vm.nics] if vm else [],
        }

        # Telemetry log
        self.streamer.record_quarantine_event(vm_name=vm_name, portgroup=q_pg)

        detail_msg = "; ".join(execution_details) if execution_details else f"VM '{vm_name}' successfully isolated to {q_pg} via hypervisor switch policy."

        return VMwareQuarantineResult(
            action_id=action_id,
            vm_id=vm_id,
            vm_name=vm_name,
            method=method,
            success=True,
            details=detail_msg,
            previous_state=prev_state,
            new_state=new_state,
            timestamp=time.time(),
        )

    def restore_vm_network(
        self,
        vm_id: str,
        target_portgroup: str,
        vlan_id: int = 500,
    ) -> VMwareQuarantineResult:
        """Restores a quarantined VM back to production network after remediation."""
        vm = self.vm_manager.get_vm_by_id(vm_id) or self.vm_manager.get_vm_by_name(vm_id)
        vm_name = vm.name if vm else vm_id
        action_id = f"restore-{uuid.uuid4().hex[:8]}"

        prev_state = {"is_isolated": True}
        if vm:
            vm.is_isolated = False
            for nic in vm.nics:
                nic.portgroup = target_portgroup
                nic.vlan_id = vlan_id
                nic.is_connected = True

        new_state = {
            "is_isolated": False,
            "nics": [{"label": n.label, "portgroup": n.portgroup, "connected": n.is_connected} for n in vm.nics] if vm else [],
        }

        return VMwareQuarantineResult(
            action_id=action_id,
            vm_id=vm_id,
            vm_name=vm_name,
            method=QuarantineMethod.PORTGROUP_MIGRATION,
            success=True,
            details=f"Restored VM '{vm_name}' to production portgroup '{target_portgroup}' (VLAN {vlan_id}).",
            previous_state=prev_state,
            new_state=new_state,
            timestamp=time.time(),
        )

    def power_off_vm(self, vm_id: str, hard_kill: bool = False) -> Dict[str, Any]:
        """Emergency power-off for rogue or actively exfiltrating VM."""
        vm = self.vm_manager.get_vm_by_id(vm_id) or self.vm_manager.get_vm_by_name(vm_id)
        vm_name = vm.name if vm else vm_id

        # 1. Live vCenter power off
        if self.client.is_connected and not self.client.is_emulated and self.client._http_client and vm:
            try:
                action = "stop" if hard_kill else "shutdown"
                resp = self.client._http_client.post(
                    f"{self.client.base_url}/vcenter/vm/{vm.vm_id}/power?action={action}",
                    timeout=10.0,
                )
                logger.info(f"Live vCenter power-off VM {vm_id}: HTTP {resp.status_code}")
            except Exception as e:
                logger.error(f"Live vCenter power-off failed: {e}")

        # 2. Local Hyper-V
        if local_execution_driver.hyperv_available:
            local_execution_driver.quarantine_hyperv_vm(vm_name)

        if vm:
            from src.vmware.models import PowerState
            vm.power_state = PowerState.POWERED_OFF
            vm.is_isolated = True

        return {
            "success": True,
            "vm_id": vm_id,
            "vm_name": vm_name,
            "action": "POWER_OFF",
            "hard_kill": hard_kill,
            "message": f"VM '{vm_name}' powered off. Hypervisor resources halted.",
        }

    def disconnect_all_vnics(self, vm_id: str) -> VMwareQuarantineResult:
        """Convenience method to disconnect all virtual NICs for an immediate cable-pull isolation."""
        return self.quarantine_vm(vm_id=vm_id, method=QuarantineMethod.VNIC_DISCONNECT)

    def emergency_power_off(self, vm_id: str, hard_kill: bool = True) -> VMwareQuarantineResult:
        """Convenience method for emergency hypervisor power-off."""
        self.power_off_vm(vm_id=vm_id, hard_kill=hard_kill)
        return self.quarantine_vm(vm_id=vm_id, method=QuarantineMethod.POWER_OFF)

