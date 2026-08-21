"""
FastAPI Backend Integration & Endpoint Test Suite.
Verifies all REST API endpoints for graphs, prediction, explainability,
counterfactual defense, and experiments.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.graph_manager import graph_manager


@pytest.fixture
def client():
    return TestClient(app)


class TestAPIEndpoints:
    def test_health_and_root(self, client):
        res_root = client.get("/")
        assert res_root.status_code == 200
        assert res_root.json()["system"] == "AegisPath"

        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

    def test_list_graphs(self, client):
        res = client.get("/api/graphs")
        assert res.status_code == 200
        graphs = res.json()
        assert isinstance(graphs, list)
        assert len(graphs) > 0

    def test_get_graph_details(self, client):
        graphs = client.get("/api/graphs").json()
        target_id = graphs[0]["graph_id"]

        res = client.get(f"/api/graphs/{target_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["graph_id"] == target_id
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0

    def test_generate_synthetic_graph(self, client):
        payload = {
            "scenario_name": "test_api_gen",
            "num_computers": 15,
            "num_servers": 3,
            "num_users": 20,
            "num_ous": 2,
            "seed": 999,
        }
        res = client.post("/api/graphs/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["graph_id"] == "test_api_gen"
        assert len(data["nodes"]) > 0

    def test_predict_attack_paths(self, client):
        graphs = client.get("/api/graphs").json()
        target_id = graphs[0]["graph_id"]

        payload = {
            "graph_id": target_id,
            "model_type": "gat",
            "top_k": 3,
            "beam_width": 3,
        }
        res = client.post("/api/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["graph_id"] == target_id
        assert len(data["paths"]) >= 1
        assert data["paths"][0]["confidence_score"] >= 0.0

    def test_explain_attack_path(self, client):
        graphs = client.get("/api/graphs").json()
        target_id = graphs[0]["graph_id"]

        pred_res = client.post("/api/predict", json={"graph_id": target_id, "top_k": 1}).json()
        top_path = pred_res["paths"][0]["nodes"]

        explain_payload = {
            "graph_id": target_id,
            "path_nodes": top_path,
        }
        res = client.post("/api/explain", json=explain_payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["edge_explanations"]) == len(top_path) - 1
        assert len(data["key_findings"]) >= 1

    def test_counterfactual_defense_simulation(self, client):
        graphs = client.get("/api/graphs").json()
        target_id = graphs[0]["graph_id"]

        pred_res = client.post("/api/predict", json={"graph_id": target_id, "top_k": 1}).json()
        path_nodes = pred_res["paths"][0]["nodes"]
        pivot_node = path_nodes[1] if len(path_nodes) > 1 else 0

        sim_payload = {
            "graph_id": target_id,
            "action_type": "patch",
            "target_node_idx": pivot_node,
        }
        res = client.post("/api/defense/simulate", json=sim_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["action_type"] == "Patch Vulnerability"
        assert "delta_risk" in data

    def test_recommend_defenses(self, client):
        graphs = client.get("/api/graphs").json()
        target_id = graphs[0]["graph_id"]

        res = client.post("/api/defense/recommend", json={"graph_id": target_id, "top_n": 2})
        assert res.status_code == 200
        recs = res.json()
        assert isinstance(recs, list)

    def test_experiments_endpoints(self, client):
        res_bench = client.get("/api/experiments/benchmark")
        assert res_bench.status_code == 200
        assert "GAT (Primary)" in res_bench.json()

        res_abl = client.get("/api/experiments/ablation")
        assert res_abl.status_code == 200
        assert "E: Full Feature Set" in res_abl.json()
