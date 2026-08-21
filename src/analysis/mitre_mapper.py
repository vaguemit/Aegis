"""
MITRE ATT&CK Framework Mapping Engine.
Translates graph edges, protocols, and Active Directory security properties
into standardized MITRE ATT&CK Tactics, Techniques, and Procedures (TTPs).
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from src.data.schema import EdgeType, SecurityProperty


@dataclass
class MitreTechnique:
    """Standardized MITRE ATT&CK Technique representation."""
    tactic_id: str
    tactic_name: str
    technique_id: str
    technique_name: str
    sub_technique_id: Optional[str]
    description: str
    detection_methods: List[str]
    mitigation_ids: List[str]


class MitreAttackMapper:
    """
    Maps multi-relational graph transitions into authoritative MITRE ATT&CK TTPs.
    """

    MAPPINGS: Dict[str, MitreTechnique] = {
        "Open": MitreTechnique(
            tactic_id="TA0001",
            tactic_name="Initial Access / Lateral Movement",
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application / Remote Services",
            sub_technique_id="T1210",
            description="Adversary exploits software vulnerability (CVE) on exposed service to execute arbitrary code.",
            detection_methods=["Suricata / Snort IDS alerts on exploit signatures", "Windows EventID 4688 process creation"],
            mitigation_ids=["M1051 (Update Software)", "M1042 (Disable External Ports)"],
        ),
        "AdminTo": MitreTechnique(
            tactic_id="TA0004",
            tactic_name="Privilege Escalation",
            technique_id="T1078",
            technique_name="Valid Accounts",
            sub_technique_id="T1078.002",
            description="Adversary leverages compromised local administrative credentials to gain SYSTEM privileges on the host.",
            detection_methods=["EventID 4672 (Special privileges assigned)", "EventID 4624 (Logon Type 3 / 10)"],
            mitigation_ids=["M1026 (Privileged Account Management)", "M1018 (User Account Control)"],
        ),
        "CanRDP": MitreTechnique(
            tactic_id="TA0008",
            tactic_name="Lateral Movement",
            technique_id="T1021",
            technique_name="Remote Services",
            sub_technique_id="T1021.001",
            description="Adversary uses Remote Desktop Protocol (Port 3389) with compromised credentials to pivot across subnets.",
            detection_methods=["EventID 4624 (Logon Type 10 - RemoteInteractive)", "Network flow monitoring on TCP 3389"],
            mitigation_ids=["M1035 (Limit Access to Resource Over Network)", "M1032 (Multi-factor Authentication)"],
        ),
        "ExecuteDCOM": MitreTechnique(
            tactic_id="TA0008",
            tactic_name="Lateral Movement",
            technique_id="T1021",
            technique_name="Remote Services",
            sub_technique_id="T1021.003",
            description="Adversary leverages Distributed Component Object Model (DCOM) objects (e.g. MMC20.Application, ShellWindows) to execute remote code.",
            detection_methods=["RPC inspection on TCP port 135", "Sysmon EventID 1 (Parent process mmc.exe / explorer.exe)"],
            mitigation_ids=["M1042 (Disable or Remove Feature or Program)", "M1030 (Network Segmentation)"],
        ),
        "DCSync": MitreTechnique(
            tactic_id="TA0006",
            tactic_name="Credential Access",
            technique_id="T1003",
            technique_name="OS Credential Dumping",
            sub_technique_id="T1003.006",
            description="Adversary simulates the behavior of a Domain Controller using Directory Replication Service Remote Protocol (MS-DRSR) to harvest KRBTGT hashes.",
            detection_methods=["EventID 4662 (DS-Replication-Get-Changes-All access requested by non-DC account)"],
            mitigation_ids=["M1027 (Password Policies)", "M1015 (Active Directory Configuration)"],
        ),
        "Kerberoast": MitreTechnique(
            tactic_id="TA0006",
            tactic_name="Credential Access",
            technique_id="T1558",
            technique_name="Steal or Forge Kerberos Tickets",
            sub_technique_id="T1558.003",
            description="Adversary requests Kerberos Ticket Granting Service (TGS) tickets for user accounts with Service Principal Names (SPN) and cracks NTLM hashes offline.",
            detection_methods=["EventID 4769 (A Kerberos service ticket was requested with encryption type 0x17 - RC4)"],
            mitigation_ids=["M1027 (Password Policies - 25+ char service passwords)", "M1037 (Filter Network Traffic)"],
        ),
        "MemberOf": MitreTechnique(
            tactic_id="TA0007",
            tactic_name="Discovery",
            technique_id="T1069",
            technique_name="Permission Groups Discovery",
            sub_technique_id="T1069.002",
            description="Adversary enumerates Active Directory domain security groups and nesting hierarchies to map privilege escalation pathways.",
            detection_methods=["EventID 4661 (A handle to an AD object was requested)", "BloodHound / SharpHound LDAP query volume spikes"],
            mitigation_ids=["M1017 (Auditing and Access Control Lists)"],
        ),
    }

    @classmethod
    def get_mitre_mapping(
        cls,
        edge_type_name: str,
        has_spn: bool = False,
        is_vulnerable: bool = False,
    ) -> MitreTechnique:
        """Returns the primary MITRE ATT&CK technique for a given edge transition."""
        if has_spn and edge_type_name in ["MemberOf", "HasSID"]:
            return cls.MAPPINGS["Kerberoast"]
        if is_vulnerable and edge_type_name == "Open":
            return cls.MAPPINGS["Open"]

        return cls.MAPPINGS.get(edge_type_name, cls.MAPPINGS["MemberOf"])
