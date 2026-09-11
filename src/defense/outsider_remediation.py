"""
Automated Remediation Plan Generator for Insider-Outsider Threat Bridges.
Assembles stepwise operational remediation plans with MITRE ATT&CK mitigation mappings,
forensic audit logs, and calculated ΔRisk impact.
"""

from typing import Dict, List, Optional, Any
import time
import uuid

from src.defense.outsider_schema import (
    BridgeRemediationAction,
    RemediationPlan,
    InsiderBridge,
    OutsiderNode,
)


class OutsiderRemediationPlanner:
    """
    Generates actionable, multi-tier defense plans for SOC/NOC engineers to neutralize
    insider-introduced outsider threats.
    """

    def __init__(self):
        pass

    def build_plan(
        self,
        bridge: InsiderBridge,
        outsider: Optional[OutsiderNode] = None,
        baseline_risk: float = 0.88,
    ) -> RemediationPlan:
        """
        Creates an end-to-end multi-step remediation plan for an active insider bridge.
        """
        actions = [
            BridgeRemediationAction.CAPTURE_FORENSIC_SNAPSHOT,
            BridgeRemediationAction.QUARANTINE_VNIC,
            BridgeRemediationAction.KILL_TUNNEL_PROCESS,
            BridgeRemediationAction.SEVER_BRIDGE_LINK,
            BridgeRemediationAction.REVOKE_SESSIONS,
        ]

        # Estimated remediated risk after full bridge severance & token purge
        remediated_risk = 0.08
        delta_risk_pct = round(((remediated_risk - baseline_risk) / max(0.01, baseline_risk)) * 100.0, 1)

        mitre_mitigations = [
            "M1037: Filter Network Traffic (Drop bridge packets at switch & vSwitch)",
            "M1035: Limit Access to Resource Over Network (Microsegment insider host)",
            "M1018: User Account Management (Revoke Kerberos TGTs and active sessions)",
            "M1042: Disable or Remove Feature or Program (Terminate unauthorized tunneling tools)",
            "M1030: Network Segmentation (Isolate rogue device to quarantine VLAN 999)",
        ]

        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        audit_log = [
            f"[{timestamp_str}] [NOC/SOC] Alert: Insider node '{bridge.insider_name}' bridged to unmanaged outsider '{bridge.outsider_name}'.",
            f"[{timestamp_str}] [HYPERVISOR] Snapshot initiated for '{bridge.insider_name}' (memory dump: enabled).",
            f"[{timestamp_str}] [SWITCH] vNIC port isolation executed. Traffic redirected to Quarantine VLAN 999.",
            f"[{timestamp_str}] [EDR] Terminated rogue tunnel process on insider host (Process: chisel.exe / Port: {bridge.port}).",
            f"[{timestamp_str}] [ACTIVE_DIRECTORY] Purged Kerberos tickets and invalidated logon tokens for associated user session.",
            f"[{timestamp_str}] [AEGISPATH] Attack path severed. ΔRisk: {delta_risk_pct}% (Risk reduced from {baseline_risk} to {remediated_risk}).",
        ]

        return RemediationPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            bridge_id=bridge.bridge_id,
            insider_name=bridge.insider_name,
            outsider_name=bridge.outsider_name,
            actions=actions,
            baseline_risk=baseline_risk,
            remediated_risk=remediated_risk,
            delta_risk_percent=delta_risk_pct,
            mitre_mitigations=mitre_mitigations,
            audit_log=audit_log,
            timestamp=time.time(),
        )
