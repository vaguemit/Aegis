"""
End-to-End Enterprise Defense Lifecycle Integration Test.
Simulates full post-compromise lifecycle:
1. VMware cluster discovery & graph synchronization
2. GAT attack path forecasting from rogue outsider foothold to Crown Jewels
3. Pre-quarantine forensic volatile RAM memory capture
4. Guest Operations reverse proxy process termination
5. Hypervisor network quarantine enforcement (VLAN 999)
6. Counterfactual neural re-evaluation confirming lateral movement severance (-100% risk)
"""

import pytest
import torch

from src.vmware.config import VMwareConfig
from src.vmware.client import VMwareClient
from src.vmware.graph_sync import VMwareGraphSynchronizer
from src.vmware.rogue_detector import VMwareRogueDetector
from src.vmware.forensics import VMwareForensicManager
from src.vmware.guest_ops import VMwareGuestOpsManager
from src.vmware.quarantine import VMwareActiveQuarantine
from src.vmware.models import QuarantineMethod
from src.models.gat import GATModel
from src.search.beam_search import ConstrainedBeamSearch


class TestEndToEndLifecycle:
    def test_complete_enterprise_defense_lifecycle(self):
        # 1. Connect & Sync VMware Cluster
        cfg = VMwareConfig(enable_emulation_fallback=True)
        client = VMwareClient(cfg)
        client.connect()

        syncer = VMwareGraphSynchronizer(client)
        graph = syncer.sync_to_graph_data()
        assert graph.num_nodes >= 6

        # 2. Rogue Outsider Detection
        detector = VMwareRogueDetector(client)
        findings = detector.scan_for_rogue_vms()
        assert len(findings) >= 1
        rogue_vm_name = findings[0]["vm_name"]

        # 3. GAT Attack Path Forecasting
        gat = GATModel(in_features=20, hidden_dim=64, out_dim=64, num_heads=4, num_layers=2)
        gat.eval()
        with torch.no_grad():
            pred_probs = gat(graph.x_matrix, graph.adj_tensor)

        beam_search = ConstrainedBeamSearch(beam_width=3, max_hops=8)
        initial_paths = beam_search.search(
            edge_probs=pred_probs,
            adj_tensor=graph.adj_tensor,
            x_matrix=graph.x_matrix,
            source_idx=graph.source_idx,
            target_idx=graph.target_idx,
        )
        assert len(initial_paths) >= 1

        # 4. Forensic Snapshot with Volatile RAM Dump
        forensics = VMwareForensicManager(client)
        snap = forensics.capture_forensic_snapshot(rogue_vm_name, include_memory=True)
        assert snap.memory_dump_included is True

        # 5. Guest Operations Process Termination
        guest_ops = VMwareGuestOpsManager(client)
        term_res = guest_ops.terminate_all_rogue_processes(rogue_vm_name)
        assert term_res["status"] == "ALL_TERMINATED"

        # 6. Hypervisor Active Defense Quarantine
        quarantine = VMwareActiveQuarantine(client)
        q_res = quarantine.quarantine_vm(rogue_vm_name, method=QuarantineMethod.PORTGROUP_MIGRATION)
        assert q_res.success is True

        # 7. Post-Defense GAT Neural Re-evaluation
        remediated_graph = syncer.sync_delta_update(graph, vm_index=graph.source_idx, action="ISOLATE")
        assert remediated_graph.adj_tensor[graph.source_idx].sum().item() == 0.0

        with torch.no_grad():
            remediated_probs = gat(remediated_graph.x_matrix, remediated_graph.adj_tensor)

        post_paths = beam_search.search(
            edge_probs=remediated_probs,
            adj_tensor=remediated_graph.adj_tensor,
            x_matrix=remediated_graph.x_matrix,
            source_idx=remediated_graph.source_idx,
            target_idx=remediated_graph.target_idx,
        )

        # Confirm that the adversary cannot reach the Crown Jewel target (path severed)
        assert any(p.nodes[-1] == graph.target_idx for p in post_paths) is False
        assert post_paths[0].hop_count == 0
