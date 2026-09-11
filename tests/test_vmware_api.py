"""
Unit and Integration Tests for VMware vSphere REST API Endpoints.
Tests connection status, cluster inventory, quarantine actions, snapshots, and graph sync.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestVMwareAPI:
    def test_vmware_status(self, client):
        resp = client.get("/api/vmware/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "connected" in data
        assert "host" in data

    def test_vmware_inventory(self, client):
        resp = client.get("/api/vmware/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hosts"] >= 2
        assert data["total_vms"] >= 6
        assert len(data["vms"]) >= 6

    def test_network_topology(self, client):
        resp = client.get("/api/vmware/network-topology")
        assert resp.status_code == 200
        data = resp.json()
        assert "vswitches" in data
        assert "portgroups" in data

    def test_rogue_vms_detection(self, client):
        resp = client.get("/api/vmware/rogue-vms")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_security_audit(self, client):
        resp = client.get("/api/vmware/audit-security")
        assert resp.status_code == 200
        data = resp.json()
        assert "compliant" in data

    def test_quarantine_and_restore(self, client):
        # Quarantine
        q_resp = client.post(
            "/api/vmware/quarantine",
            json={"vm_id": "VM-WS01", "method": "PORTGROUP_MIGRATION", "quarantine_portgroup": "Quarantine_VLAN_999"},
        )
        assert q_resp.status_code == 200
        q_data = q_resp.json()
        assert q_data["success"] is True
        assert q_data["vm_name"] == "VM-WS01"

        # Restore
        r_resp = client.post(
            "/api/vmware/restore",
            json={"vm_id": "VM-WS01", "target_portgroup": "Workstations-VLAN500", "vlan_id": 500},
        )
        assert r_resp.status_code == 200
        assert r_resp.json()["success"] is True

    def test_snapshot_capture(self, client):
        s_resp = client.post(
            "/api/vmware/snapshot",
            json={"vm_id": "VM-DC01", "snapshot_name": "Test_Forensic_Snap", "include_memory": True},
        )
        assert s_resp.status_code == 200
        s_data = s_resp.json()
        assert s_data["success"] is True
        assert s_data["memory_dump_included"] is True

    def test_guest_ops_and_kill(self, client):
        p_resp = client.get("/api/vmware/guest-ops/processes?vm_id=VM-ROGUE-SHADOW")
        assert p_resp.status_code == 200
        p_data = p_resp.json()
        assert p_data["total_processes"] >= 4

        k_resp = client.post("/api/vmware/guest-ops/terminate-rogue", json={"vm_id": "VM-ROGUE-SHADOW"})
        assert k_resp.status_code == 200
        assert k_resp.json()["status"] == "ALL_TERMINATED"

    def test_sync_graph_to_aegispath(self, client):
        sync_resp = client.post("/api/vmware/sync-graph")
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["success"] is True
        assert sync_data["num_nodes"] >= 6

    def test_telemetry_events(self, client):
        ev_resp = client.get("/api/vmware/events?limit=10")
        assert ev_resp.status_code == 200
        assert isinstance(ev_resp.json(), list)
