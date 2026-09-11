"""
VMware Hypervisor Network Security Policy Auditor.
Audits virtual switches for promiscuous packet sniffing, MAC address spoofing,
and forged transmit vulnerabilities.
"""

from typing import Dict, List, Any
import logging

from src.vmware.client import VMwareClient
from src.vmware.discovery import VMwareTopologyDiscoverer

logger = logging.getLogger("aegispath.vmware.security_auditor")


class VMwareSecurityAuditor:
    """
    Scans vSphere network portgroups for compliance with enterprise zero-trust baseline policies.
    """

    def __init__(self, client: VMwareClient):
        self.client = client
        self.discoverer = VMwareTopologyDiscoverer(client)

    def audit_security_policies(self) -> Dict[str, Any]:
        """Performs security compliance scan across all vSwitches and portgroups."""
        report = self.discoverer.discover_cluster()
        violations = []

        for sw in report.vswitches:
            for pg in sw.portgroups:
                if pg.promiscuous_mode:
                    violations.append({
                        "resource": f"{sw.name}/{pg.name}",
                        "policy": "PROMISCUOUS_MODE",
                        "status": "NON_COMPLIANT",
                        "risk": "HIGH",
                        "remediation": f"Set-VirtualPortGroup -Name '{pg.name}' -PromiscuousMode Reject",
                    })
                if pg.mac_changes_allowed:
                    violations.append({
                        "resource": f"{sw.name}/{pg.name}",
                        "policy": "MAC_ADDRESS_CHANGES",
                        "status": "NON_COMPLIANT",
                        "risk": "MEDIUM",
                        "remediation": f"Set-VirtualPortGroup -Name '{pg.name}' -MacChanges Reject",
                    })
                if pg.forged_transmits_allowed:
                    violations.append({
                        "resource": f"{sw.name}/{pg.name}",
                        "policy": "FORGED_TRANSMITS",
                        "status": "NON_COMPLIANT",
                        "risk": "MEDIUM",
                        "remediation": f"Set-VirtualPortGroup -Name '{pg.name}' -ForgedTransmits Reject",
                    })

        is_compliant = len(violations) == 0
        return {
            "compliant": is_compliant,
            "total_violations": len(violations),
            "violations": violations,
            "recommendation": "Enforce zero-trust L2 security baseline across all vSwitches." if not is_compliant else "All vSwitch portgroup security policies adhere to baseline.",
        }
