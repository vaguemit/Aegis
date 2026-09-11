"""
VMware vCenter Event Stream and Hypervisor Syslog Telemetry Generator.
Listens to and formats vSphere events (vNIC reconfigurations, migrations, power state changes)
into structured audit logs and RFC 5424 compliant Syslog entries.
"""

from typing import Dict, List, Optional, Any
import time
import collections

from src.vmware.models import VMwareVMInfo


class VMwareTelemetryStreamer:
    """
    Maintains live stream of hypervisor audit events and formats Syslog messages.
    """

    def __init__(self, max_history: int = 100):
        self._history: collections.deque = collections.deque(maxlen=max_history)

    def record_event(
        self,
        event_type: str,
        vm_name: str,
        message: str,
        severity: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Records a new vSphere event and appends to the audit history."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        syslog_line = f"<14>1 {timestamp} esxi-cluster vCenter - {event_type} [vm=\"{vm_name}\" sev=\"{severity}\"] {message}"

        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "vm_name": vm_name,
            "severity": severity,
            "message": message,
            "syslog": syslog_line,
            "metadata": metadata or {},
        }
        self._history.append(event)
        return event

    def record_quarantine_event(self, vm_name: str, portgroup: str) -> Dict[str, Any]:
        """Emits an event when a VM is placed into network quarantine."""
        return self.record_event(
            event_type="NetworkAdapterReconfiguredEvent",
            vm_name=vm_name,
            message=f"Active Defense: vNIC isolated and re-assigned to quarantine portgroup '{portgroup}'.",
            severity="WARNING",
            metadata={"action": "QUARANTINE", "portgroup": portgroup},
        )

    def record_rogue_detected_event(self, vm_name: str, ip: str) -> Dict[str, Any]:
        """Emits an alert when an unmanaged outsider VM is identified."""
        return self.record_event(
            event_type="VmRogueDetectedEvent",
            vm_name=vm_name,
            message=f"Threat Alert: Unauthorized outsider VM '{vm_name}' detected on internal subnet (IP: {ip}).",
            severity="CRITICAL",
            metadata={"threat": "OUTSIDER_NODE", "ip": ip},
        )

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns the most recent hypervisor telemetry events."""
        events = list(self._history)
        return events[-limit:]
