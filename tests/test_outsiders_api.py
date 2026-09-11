"""
Unit Tests for Outsider Threat and Insider Bridge API Endpoints.
Verifies bridge injection, detection, severance, and remediation planning routes.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    c = TestClient(app)
    # Ensure a baseline graph is loaded
    c.post("/api/vmware/sync-graph")
    return c


class TestOutsidersAPI:
    def test_inject_outsider_threat(self, client):
        resp = client.post(
            "/api/outsiders/inject",
            json={"threat_vector": "REVERSE_TUNNEL"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "outsider_node" in data
        assert "bridge" in data
        assert "risk_elevation" in data
        assert data["risk_elevation"]["elevated_risk"] >= data["risk_elevation"]["baseline_risk"]

    def test_detect_anomalous_bridges(self, client):
        # Inject one first
        client.post("/api/outsiders/inject", json={"threat_vector": "DUAL_HOMED_NIC"})
        resp = client.get("/api/outsiders/detect")
        assert resp.status_code == 200
        bridges = resp.json()
        assert isinstance(bridges, list)
        assert len(bridges) >= 1

    def test_sever_outsider_bridge(self, client):
        inj_resp = client.post("/api/outsiders/inject", json={"threat_vector": "SHADOW_VM"})
        new_nodes = inj_resp.json()["new_graph_nodes"]
        outsider_idx = new_nodes - 1

        sever_resp = client.post(
            "/api/outsiders/sever",
            json={"insider_node_idx": 0, "outsider_node_idx": outsider_idx},
        )
        assert sever_resp.status_code == 200
        data = sever_resp.json()
        assert data["success"] is True
        assert data["metrics"]["status"] == "SUCCESS"

    def test_isolate_insider_node(self, client):
        iso_resp = client.post(
            "/api/outsiders/isolate-insider",
            json={"insider_node_idx": 1},
        )
        assert iso_resp.status_code == 200
        assert iso_resp.json()["success"] is True

    def test_remediation_plan_generation(self, client):
        plan_resp = client.get("/api/outsiders/remediation-plan?insider_idx=0&outsider_idx=1")
        assert plan_resp.status_code == 200
        plan = plan_resp.json()
        assert "plan_id" in plan
        assert len(plan["actions"]) >= 4
        assert len(plan["mitre_mitigations"]) >= 3
        assert len(plan["audit_log"]) >= 4
