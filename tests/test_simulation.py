"""
Unit Tests for Virtual Machine Infrastructure & Attack Playback Simulation.
"""

import pytest
from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.simulation.vm_engine import EnterpriseVMSimulator, VMState
from src.simulation.attack_player import LiveAttackPlaybackEngine
from src.models.gat import GATModel


@pytest.fixture
def sample_network():
    gen = SyntheticEnterpriseGenerator(num_computers=10, num_servers=3, num_users=15, seed=42)
    return gen.generate()


class TestVMSimulation:
    def test_build_vms_from_graph(self, sample_network):
        sim = EnterpriseVMSimulator()
        vms = sim.build_vms_from_graph(sample_network)

        assert len(vms) == sample_network.num_nodes
        assert len(sim.hypervisors) >= 2

        # Check VM attributes
        dc_vms = [v for v in vms if v.is_domain_controller]
        assert len(dc_vms) >= 1
        assert dc_vms[0].ram_gb >= 16
        assert len(dc_vms[0].network_adapters) >= 1

    def test_live_attack_playback_engine(self, sample_network):
        sim = EnterpriseVMSimulator()
        sim.build_vms_from_graph(sample_network)

        player = LiveAttackPlaybackEngine(sim)
        gat = GATModel(in_features=20, hidden_dim=32, out_dim=32, num_heads=2, num_layers=2)
        probs = gat(sample_network.x_matrix, sample_network.adj_tensor)

        path = sample_network.attack_path_nodes
        events = player.prepare_attack_timeline(
            path_nodes=path,
            node_names=sample_network.node_names,
            adj_tensor=sample_network.adj_tensor,
            edge_probs=probs,
        )

        assert len(events) == len(path) - 1
        for ev in events:
            assert ev.step_number >= 1
            assert len(ev.source_ip) > 0
            assert len(ev.target_ip) > 0
            assert len(ev.syslog_entry) > 0
            assert ev.mitre_technique_id.startswith("T1")
