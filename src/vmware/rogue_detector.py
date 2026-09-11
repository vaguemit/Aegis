"""
VMware Rogue and Outsider Virtual Machine Detector.
Scans vSphere inventory for shadow IT, unauthorized virtual machines,
non-domain joined endpoints, and malicious dual-homed network bridges.
"""

from typing import Dict, List, Optional, Any
import logging

from src.vmware.client import VMwareClient
from src.vmware.models import VMwareVMInfo
from src.vmware.discovery import VMwareTopologyDiscoverer

logger = logging.getLogger("aegispath.vmware.rogue_detector")


class VMwareRogueDetector:
    """
    Audits VMware virtual machines to identify outsider nodes and unauthorized bridges.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)

    def scan_for_rogue_vms(self) -> List[Dict[str, Any]]:
        """
        Performs multi-criteria security audit across all VMs in the cluster.
        Returns list of detected rogue / outsider candidates with threat explanations.
        """
        report = self.discoverer.discover_cluster()
        rogue_findings = []

        for vm in report.vms:
            risk_indicators = []
            confidence = 0.0

            # 1. Non-domain joined on production subnet
            if not vm.is_domain_joined:
                risk_indicators.append("NON_DOMAIN_JOINED: Machine is not enrolled in Active Directory domain.")
                confidence += 0.40

            # 2. Suspicious Guest OS (e.g. Kali, Parrot, BlackArch)
            os_lower = vm.guest_os.lower()
            if any(k in os_lower for k in ["kali", "parrot", "blackarch", "pentest"]):
                risk_indicators.append(f"OFFENSIVE_SECURITY_OS: Guest OS is identified as '{vm.guest_os}'.")
                confidence += 0.50

            # 3. Explicit outsider or unauthorized tag
            if vm.is_outsider or "unauthorized" in vm.tags:
                risk_indicators.append("UNAUTHORIZED_TAG: Asset marked as unmanaged shadow IT.")
                confidence += 0.45

            # 4. Multi-homed bridge inspection (connecting multiple VLANs)
            vlan_ids = set()
            for nic in vm.nics:
                vlan_ids.add(nic.vlan_id)
            if len(vlan_ids) > 1:
                risk_indicators.append(f"MULTI_HOMED_BRIDGE: VM bridges {len(vlan_ids)} distinct VLANs ({list(vlan_ids)}).")
                confidence += 0.35

            # 5. Promiscuous mode enabled on vNIC
            for nic in vm.nics:
                if nic.is_promiscuous:
                    risk_indicators.append(f"PROMISCUOUS_SNIFFING: Adapter '{nic.label}' configured in promiscuous mode.")
                    confidence += 0.30

            if confidence >= 0.50 or vm.is_outsider:
                confidence = min(0.99, confidence)
                finding = {
                    "vm_id": vm.vm_id,
                    "vm_name": vm.name,
                    "ip_address": vm.ip_address,
                    "guest_os": vm.guest_os,
                    "host_id": vm.host_id,
                    "threat_confidence": round(confidence, 3),
                    "severity": "CRITICAL" if confidence > 0.8 else "HIGH",
                    "risk_indicators": risk_indicators,
                    "recommended_action": "QUARANTINE_VNIC_VLAN_999",
                }
                rogue_findings.append(finding)

        return rogue_findings
