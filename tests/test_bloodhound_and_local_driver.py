"""
Tests for BloodHound Active Directory graph ingestion and local hypervisor execution drivers.
"""

import pytest
import torch
from src.data.bloodhound_loader import BloodHoundLoader, create_realistic_enterprise_ad_sample
from src.vmware.local_driver import local_execution_driver
from src.vmware.guest_ops import VMwareGuestOpsManager
from src.vmware.quarantine import VMwareActiveQuarantine
from src.vmware.client import VMwareClient
from src.vmware.config import VMwareConfig
from src.data.schema import EntityType, SecurityProperty, PROPERTY_TO_IDX, ENTITY_TO_IDX


def test_bloodhound_realistic_sample():
    g = create_realistic_enterprise_ad_sample()
    assert g.num_nodes == 16
    assert g.x_matrix.shape == (16, 20)
    assert g.adj_tensor.shape == (16, 16, 16)
    assert g.source_idx is not None
    assert g.target_idx is not None
    assert g.node_names is not None
    assert "DC01.CORP.LOCAL" in g.node_names
    assert "DOMAIN ADMINS@CORP.LOCAL" in g.node_names


def test_bloodhound_custom_ingest():
    loader = BloodHoundLoader()
    custom_data = {
        "data": [
            {"type": "computer", "ObjectIdentifier": "COMP-1", "Properties": {"name": "WS01.CORP.LOCAL", "operatingsystem": "Windows 10"}},
            {"type": "user", "ObjectIdentifier": "USER-1", "Properties": {"name": "ALICE@CORP.LOCAL"}},
            {"type": "group", "ObjectIdentifier": "GRP-1", "Properties": {"name": "DOMAIN ADMINS@CORP.LOCAL", "highvalue": True}},
        ]
    }
    custom_data["data"][1]["MemberOf"] = ["GRP-1"]
    custom_data["data"][1]["AdminTo"] = ["COMP-1"]

    loader.ingest_json_dict(custom_data)
    graph = loader.build_graph(scenario_name="unit_test_bh")

    assert graph.num_nodes == 3
    assert graph.x_matrix.shape == (3, 20)
    assert graph.adj_tensor.shape == (3, 3, 16)


def test_local_execution_driver_status():
    status = local_execution_driver.get_status()
    assert "os" in status
    assert "can_terminate_local_processes" in status
    assert status["can_terminate_local_processes"] is True


def test_local_running_processes():
    procs = local_execution_driver.list_running_processes()
    assert isinstance(procs, list)
    assert len(procs) > 0
    first = procs[0]
    assert "pid" in first
    assert "name" in first


def test_guest_ops_with_local_execution():
    config = VMwareConfig(enable_emulation_fallback=True)
    client = VMwareClient(config)
    client.connect()
    guest_ops = VMwareGuestOpsManager(client)

    # Test local process query
    local_procs = guest_ops.list_guest_processes("local")
    assert len(local_procs) > 0
    assert any(p.pid > 0 for p in local_procs)

    # Test emulated dynamic process table
    vm_procs = guest_ops.list_guest_processes("VM-DC01")
    assert len(vm_procs) > 0
    initial_count = len(vm_procs)

    # Terminate one process
    target_pid = vm_procs[0].pid
    term_res = guest_ops.terminate_guest_process("VM-DC01", target_pid)
    assert term_res["success"] is True

    # Confirm it does not resurrect
    updated_procs = guest_ops.list_guest_processes("VM-DC01")
    assert len(updated_procs) == initial_count - 1
    assert not any(p.pid == target_pid for p in updated_procs)
