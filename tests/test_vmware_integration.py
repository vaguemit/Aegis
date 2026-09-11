"""
Unit & Integration Test Suite for AegisPath VMware vSphere Integration.
Validates client sessions, cluster discovery, vSwitch topology mapping,
rogue VM detection, network quarantine, digital forensics, guest ops, and graph synchronization.
"""

import pytest
import torch

from src.vmware.config import VMwareConfig
from src.vmware.client import VMwareClient
from src.vmware.emulator import VMwareClusterEmulator
from src.vmware.discovery import VMwareTopologyDiscoverer
from src.vmware.vm_manager import VMwareVMManager
from src.vmware.network_mapper import VMwareNetworkMapper
from src.vmware.security_auditor import VMwareSecurityAuditor
from src.vmware.rogue_detector import VMwareRogueDetector
from src.vmware.bridge_detector import VMwareBridgeDetector
from src.vmware.quarantine import VMwareActiveQuarantine
from src.vmware.forensics import VMwareForensicManager
from src.vmware.guest_ops import VMwareGuestOpsManager
from src.vmware.telemetry import VMwareTelemetryStreamer
from src.vmware.graph_sync import VMwareGraphSynchronizer
from src.vmware.models import QuarantineMethod, PowerState
from src.data.schema import NetworkGraphData


@pytest.fixture
def vmware_client():
    cfg = VMwareConfig(enable_emulation_fallback=True)
    client = VMwareClient(cfg)
    client.connect()
    return client


class TestVMwareIntegration:
    def test_config_loader(self):
        cfg = VMwareConfig.from_env()
        assert cfg.port == 443
        assert cfg.quarantine_vlan == 999
        assert "Quarantine" in cfg.quarantine_portgroup

    def test_client_connection(self, vmware_client):
        assert vmware_client.is_connected is True
        assert vmware_client.session_id is not None
        status = vmware_client.get_status()
        assert status["connected"] is True
        assert status["session_active"] is True

    def test_cluster_discovery(self, vmware_client):
        discoverer = VMwareTopologyDiscoverer(vmware_client)
        report = discoverer.discover_cluster()
        assert report.total_hosts >= 2
        assert report.total_vms >= 6
        assert len(report.vswitches) >= 2

    def test_vm_manager(self, vmware_client):
        mgr = VMwareVMManager(vmware_client)
        vms = mgr.list_all_vms()
        assert len(vms) >= 6

        dc = mgr.get_vm_by_name("VM-DC01")
        assert dc is not None
        assert dc.cpu_count == 8
        assert "10.0.10" in dc.ip_address

    def test_network_mapper(self, vmware_client):
        mapper = VMwareNetworkMapper(vmware_client)
        topo = mapper.get_network_topology()
        assert len(topo["vswitches"]) >= 2
        assert "AD-Core-VLAN100" in topo["portgroups"]
        assert "Quarantine_VLAN_999" in topo["portgroups"]

    def test_security_auditor(self, vmware_client):
        auditor = VMwareSecurityAuditor(vmware_client)
        audit = auditor.audit_security_policies()
        assert "compliant" in audit
        assert "violations" in audit

    def test_rogue_detector(self, vmware_client):
        detector = VMwareRogueDetector(vmware_client)
        findings = detector.scan_for_rogue_vms()
        assert len(findings) >= 1
        rogue_vm = next((f for f in findings if "SHADOW" in f["vm_name"] or "ROGUE" in f["vm_name"]), None)
        assert rogue_vm is not None
        assert rogue_vm["threat_confidence"] > 0.5
        assert rogue_vm["severity"] in ("HIGH", "CRITICAL")

    def test_bridge_detector(self, vmware_client):
        detector = VMwareBridgeDetector(vmware_client)
        bridges = detector.find_bridging_vms()
        assert isinstance(bridges, list)

    def test_active_quarantine_vlan(self, vmware_client):
        streamer = VMwareTelemetryStreamer()
        quarantine = VMwareActiveQuarantine(vmware_client, streamer)
        res = quarantine.quarantine_vm("VM-WS01", method=QuarantineMethod.PORTGROUP_MIGRATION)
        assert res.success is True
        assert res.method == QuarantineMethod.PORTGROUP_MIGRATION
        assert res.new_state["is_isolated"] is True

        # Test restoration
        restore_res = quarantine.restore_vm_network("VM-WS01", target_portgroup="Workstations-VLAN500")
        assert restore_res.success is True
        assert restore_res.new_state["is_isolated"] is False

    def test_active_quarantine_vnic_disconnect(self, vmware_client):
        quarantine = VMwareActiveQuarantine(vmware_client)
        res = quarantine.disconnect_all_vnics("VM-WS02")
        assert res.success is True
        assert res.method == QuarantineMethod.VNIC_DISCONNECT

    def test_emergency_power_off(self, vmware_client):
        quarantine = VMwareActiveQuarantine(vmware_client)
        res = quarantine.emergency_power_off("VM-WS02")
        assert res.success is True
        assert res.method == QuarantineMethod.POWER_OFF

    def test_forensic_snapshot_memory_dump(self, vmware_client):
        forensics = VMwareForensicManager(vmware_client)
        snap = forensics.capture_forensic_snapshot("VM-DC01", include_memory=True)
        assert snap.memory_dump_included is True
        assert "AegisPath_Forensic" in snap.name
        assert len(forensics.get_snapshots("VM-DC01")) == 1

    def test_guest_ops_process_inspection_and_killing(self, vmware_client):
        guest_ops = VMwareGuestOpsManager(vmware_client)
        procs = guest_ops.list_guest_processes("VM-ROGUE-SHADOW")
        assert len(procs) >= 4

        rogue_procs = guest_ops.find_rogue_processes("VM-ROGUE-SHADOW")
        assert len(rogue_procs) >= 1
        assert "chisel" in rogue_procs[0].name.lower()

        term_res = guest_ops.terminate_all_rogue_processes("VM-ROGUE-SHADOW")
        assert term_res["status"] == "ALL_TERMINATED"
        assert term_res["terminated_count"] >= 1

    def test_telemetry_and_syslog(self):
        streamer = VMwareTelemetryStreamer()
        ev = streamer.record_quarantine_event(vm_name="VM-TEST01", portgroup="Quarantine_VLAN_999")
        assert "<14>1" in ev["syslog"]
        assert "NetworkAdapterReconfiguredEvent" in ev["event_type"]
        recent = streamer.get_recent_events(limit=5)
        assert len(recent) >= 1

    def test_graph_synchronization(self, vmware_client):
        syncer = VMwareGraphSynchronizer(vmware_client)
        graph = syncer.sync_to_graph_data()
        assert isinstance(graph, NetworkGraphData)
        assert graph.num_nodes >= 6
        assert graph.x_matrix.shape == (graph.num_nodes, 20)
        assert graph.adj_tensor.shape == (graph.num_nodes, graph.num_nodes, 16)
        assert graph.target_idx is not None

        # Test delta update
        delta_graph = syncer.sync_delta_update(graph, vm_index=0, action="ISOLATE")
        assert delta_graph.adj_tensor[0].sum().item() == 0.0
