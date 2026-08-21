"""
Live Attack Progression and Step-by-Step Telemetry Player Engine.
Simulates real-time adversarial movement across Virtual Machines,
emitting synchronized audit logs, auth events, and VM compromise state transitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import time

from src.simulation.vm_engine import EnterpriseVMSimulator, VirtualMachineInstance, VMState
from src.analysis.mitre_mapper import MitreAttackMapper


@dataclass
class LiveAttackStepEvent:
    """A single tactical lateral movement event during real-time playback."""
    step_number: int
    timestamp: str
    source_vm_id: str
    source_vm_name: str
    source_ip: str
    target_vm_id: str
    target_vm_name: str
    target_ip: str
    edge_type: str
    mitre_tactic: str
    mitre_technique_id: str
    mitre_technique_name: str
    transition_probability: float
    syslog_entry: str
    compromised_node_indices: List[int]
    status_summary: str


class LiveAttackPlaybackEngine:
    """
    Manages live interactive playback of adversarial campaigns across simulated enterprise VMs.
    """

    def __init__(self, vm_simulator: EnterpriseVMSimulator):
        self.vm_simulator = vm_simulator
        self.active_compromised_indices: List[int] = []

    def prepare_attack_timeline(
        self,
        path_nodes: List[int],
        node_names: List[str],
        adj_tensor: Any,
        edge_probs: Any,
    ) -> List[LiveAttackStepEvent]:
        """Builds a sequential timeline of live VM exploitation events."""
        events: List[LiveAttackStepEvent] = []
        self.active_compromised_indices = [path_nodes[0]] if path_nodes else []

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            u_name = node_names[u] if u < len(node_names) else f"node_{u}"
            v_name = node_names[v] if v < len(node_names) else f"node_{v}"

            src_vm_id = f"vm-{u:03d}"
            dst_vm_id = f"vm-{v:03d}"

            src_vm = self.vm_simulator.virtual_machines.get(src_vm_id)
            dst_vm = self.vm_simulator.virtual_machines.get(dst_vm_id)

            src_ip = src_vm.network_adapters[0].ip_address if src_vm else f"10.0.50.{u+10}"
            dst_ip = dst_vm.network_adapters[0].ip_address if dst_vm else f"10.0.10.{v+10}"

            # Detect relation
            rel_indices = (adj_tensor[u, v] > 0.5).nonzero(as_tuple=True)[0]
            edge_type_str = "AdminTo" if len(rel_indices) == 0 else "Open"
            if len(rel_indices) > 0:
                from src.data.schema import IDX_TO_EDGE
                edge_type_str = IDX_TO_EDGE[int(rel_indices[0].item())].value

            mitre_ttp = MitreAttackMapper.get_mitre_mapping(edge_type_str)
            prob = float(edge_probs[u, v].item()) if edge_probs is not None else 0.92

            self.active_compromised_indices.append(v)
            time_str = time.strftime("%H:%M:%S")

            syslog = (
                f"[{time_str}] EVT_SEC_AUDIT: Adversary established remote interactive session from {src_ip} ({src_vm_name_safe(src_vm, u_name)}) "
                f"to {dst_ip} ({src_vm_name_safe(dst_vm, v_name)}) using {edge_type_str} ({mitre_ttp.technique_id}). Privilege escalated to SYSTEM."
            )

            status = f"Step {i+1}: Compromised {v_name} via {mitre_ttp.technique_id} ({mitre_ttp.technique_name}) [{prob*100:.1f}% confidence]"

            event = LiveAttackStepEvent(
                step_number=i + 1,
                timestamp=time_str,
                source_vm_id=src_vm_id,
                source_vm_name=src_vm.vm_name if src_vm else f"VM-{u_name.upper()}",
                source_ip=src_ip,
                target_vm_id=dst_vm_id,
                target_vm_name=dst_vm.vm_name if dst_vm else f"VM-{v_name.upper()}",
                target_ip=dst_ip,
                edge_type=edge_type_str,
                mitre_tactic=mitre_ttp.tactic_name,
                mitre_technique_id=mitre_ttp.technique_id,
                mitre_technique_name=mitre_ttp.technique_name,
                transition_probability=prob,
                syslog_entry=syslog,
                compromised_node_indices=list(self.active_compromised_indices),
                status_summary=status,
            )
            events.append(event)

        return events


def src_vm_name_safe(vm: Optional[VirtualMachineInstance], fallback: str) -> str:
    return vm.vm_name if vm else fallback
