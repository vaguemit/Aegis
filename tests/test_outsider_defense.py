"""
Unit Tests for Outsider Node Threat Modeling, Bridge Detection, and Counterfactual Defense.
Verifies graph tensor expansion, bridge heuristics, risk elevation calculation,
and counterfactual severance actions.
"""

import pytest
import torch

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.data.schema import EdgeType, SecurityProperty, PROPERTY_TO_IDX
from src.defense.outsider_schema import (
    OutsiderType,
    BridgeMechanism,
    BridgeRemediationAction,
    OutsiderNode,
    InsiderBridge,
    RemediationPlan,
)
from src.defense.outsider_engine import OutsiderThreatEngine
from src.defense.bridge_detector import AnomalousBridgeDetector
from src.defense.risk_elevation import OutsiderRiskEvaluator
from src.defense.outsider_counterfactual import OutsiderCounterfactualEngine
from src.defense.outsider_remediation import OutsiderRemediationPlanner


@pytest.fixture
def sample_graph():
    generator = SyntheticEnterpriseGenerator(
        num_computers=10, num_servers=3, num_users=10, seed=42
    )
    return generator.generate()


class TestOutsiderDefense:
    def test_outsider_schema_and_enums(self):
        assert len(list(OutsiderType)) >= 6
        assert len(list(BridgeMechanism)) >= 6
        assert len(list(BridgeRemediationAction)) >= 5

    def test_outsider_injection_tensor_expansion(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        initial_n = sample_graph.num_nodes
        insider_idx = 2

        new_graph, outsider_meta, bridge_meta = engine.inject_outsider_node(
            graph_data=sample_graph,
            insider_idx=insider_idx,
            outsider_type=OutsiderType.REVERSE_TUNNEL,
            mechanism=BridgeMechanism.SOCKS_CHISEL_TUNNEL,
            edge_type=EdgeType.CAN_RDP,
        )

        assert new_graph.num_nodes == initial_n + 1
        assert new_graph.x_matrix.shape == (initial_n + 1, 20)
        assert new_graph.adj_tensor.shape == (initial_n + 1, initial_n + 1, 16)
        assert new_graph.has_outsider_nodes() is True
        assert len(new_graph.get_outsider_indices()) == 1
        assert new_graph.get_outsider_indices()[0] == initial_n
        assert outsider_meta.name in new_graph.node_names[-1]

    def test_specialized_threat_injections(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        
        # Test covert tunnel
        g1, o1, b1 = engine.inject_covert_tunnel(sample_graph, insider_idx=1)
        assert "REVERSE-PROXY" in o1.name
        assert b1.mechanism == BridgeMechanism.SOCKS_CHISEL_TUNNEL

        # Test dual-homed NIC
        g2, o2, b2 = engine.inject_dual_homed_nic(sample_graph, insider_idx=2)
        assert "ROGUE-TETHER" in o2.name
        assert b2.mechanism == BridgeMechanism.DUAL_HOMED_NIC

        # Test shadow VM
        g3, o3, b3 = engine.inject_shadow_vm(sample_graph, insider_idx=3)
        assert "SHADOW-VM" in o3.name
        assert b3.mechanism == BridgeMechanism.VMWARE_SHARED_NAT

    def test_anomalous_bridge_detector(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        injected_g, _, _ = engine.inject_covert_tunnel(sample_graph, insider_idx=2)

        detector = AnomalousBridgeDetector(anomaly_threshold=0.6)
        detected = detector.detect_bridges(injected_g)

        assert len(detected) >= 1
        found_bridge = any(d["insider_node_idx"] == 2 for d in detected)
        assert found_bridge is True

    def test_risk_elevation_scoring(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        injected_g, o_meta, b_meta = engine.inject_covert_tunnel(sample_graph, insider_idx=2)

        evaluator = OutsiderRiskEvaluator()
        result = evaluator.evaluate_risk_elevation(
            baseline_graph=sample_graph,
            injected_graph=injected_g,
            outsider_idx=injected_g.num_nodes - 1,
            insider_idx=2,
        )

        assert "baseline_risk" in result
        assert "elevated_risk" in result
        assert result["elevated_risk"] >= result["baseline_risk"]
        assert result["risk_increase_percent"] >= 0.0

    def test_counterfactual_bridge_severance(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        injected_g, _, _ = engine.inject_covert_tunnel(sample_graph, insider_idx=2)
        outsider_idx = injected_g.num_nodes - 1

        cf_engine = OutsiderCounterfactualEngine()
        severed_g, metrics = cf_engine.sever_bridge(injected_g, insider_idx=2, outsider_idx=outsider_idx)

        assert metrics["status"] == "SUCCESS"
        assert metrics["edges_severed"] >= 1
        # Check that edge between 2 and outsider_idx is zeroed
        assert severed_g.adj_tensor[2, outsider_idx].sum().item() == 0.0
        assert severed_g.adj_tensor[outsider_idx, 2].sum().item() == 0.0

    def test_counterfactual_insider_host_isolation(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        injected_g, _, _ = engine.inject_covert_tunnel(sample_graph, insider_idx=2)

        cf_engine = OutsiderCounterfactualEngine()
        isolated_g, metrics = cf_engine.isolate_insider_host(injected_g, insider_idx=2)

        assert metrics["status"] == "SUCCESS"
        assert isolated_g.adj_tensor[2, :].sum().item() == 0.0
        assert isolated_g.adj_tensor[:, 2].sum().item() == 0.0

    def test_remediation_planner_output(self, sample_graph):
        engine = OutsiderThreatEngine(seed=42)
        _, o_meta, b_meta = engine.inject_covert_tunnel(sample_graph, insider_idx=2)

        planner = OutsiderRemediationPlanner()
        plan = planner.build_plan(bridge=b_meta, outsider=o_meta, baseline_risk=0.85)

        assert isinstance(plan, RemediationPlan)
        assert len(plan.actions) == 5
        assert len(plan.mitre_mitigations) >= 4
        assert plan.delta_risk_percent < 0.0
        assert len(plan.audit_log) >= 5
