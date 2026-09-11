"""
Insider-Introduces-Outsider Threat Demonstration & Counterfactual Severance CLI.
Demonstrates end-to-end detection, risk elevation calculation, and automated mitigation
when an insider asset bridges an unmanaged external node into the domain.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.synthetic_generator import SyntheticEnterpriseGenerator
from src.defense.outsider_schema import OutsiderType, BridgeMechanism
from src.defense.outsider_engine import OutsiderThreatEngine
from src.defense.bridge_detector import AnomalousBridgeDetector
from src.defense.risk_elevation import OutsiderRiskEvaluator
from src.defense.outsider_counterfactual import OutsiderCounterfactualEngine
from src.defense.outsider_remediation import OutsiderRemediationPlanner


def main():
    print("=" * 72)
    print("[AegisPath] Threat Scenario: Insider Asset Introduces Outsider Node")
    print("=" * 72)

    # 1. Generate Baseline Graph
    print("\n[Step 1] Loading Enterprise Active Directory Topology...")
    generator = SyntheticEnterpriseGenerator(num_computers=20, num_servers=5, num_users=25, seed=42)
    baseline_graph = generator.generate()
    print(f"[+] Baseline Graph: {baseline_graph.graph_id} ({baseline_graph.num_nodes} nodes, {int((baseline_graph.adj_tensor > 0).sum().item())} edges)")
    print(f"[+] Crown Jewel Target: {baseline_graph.node_names[baseline_graph.target_idx]}")

    # 2. Insider Introduces Outsider Node
    insider_idx = 4
    insider_name = baseline_graph.node_names[insider_idx]
    print(f"\n[Step 2] Insider Machine '{insider_name}' introduces Rogue External Node...")
    engine = OutsiderThreatEngine(seed=42)
    injected_graph, outsider_meta, bridge_meta = engine.inject_covert_tunnel(
        graph_data=baseline_graph,
        insider_idx=insider_idx,
    )
    print(f"[!] Anomalous Node Injected: {outsider_meta.name}")
    print(f"    - Outsider IP: {outsider_meta.ip_address} | MAC: {outsider_meta.mac_address}")
    print(f"    - Threat Vector: {outsider_meta.outsider_type.value}")
    print(f"    - Bridge Mechanism: {bridge_meta.mechanism.value} (Port: {bridge_meta.port})")
    print(f"    - Graph Expanded to {injected_graph.num_nodes} nodes.")

    # 3. Risk Elevation Evaluation
    print("\n[Step 3] Evaluating Risk Elevation Delta (Delta-Risk)...")
    evaluator = OutsiderRiskEvaluator()
    risk_report = evaluator.evaluate_risk_elevation(
        baseline_graph=baseline_graph,
        injected_graph=injected_graph,
        outsider_idx=injected_graph.num_nodes - 1,
        insider_idx=insider_idx,
    )
    print(f"    - Baseline Enterprise Risk: {risk_report['baseline_risk'] * 100:.1f}%")
    print(f"    - Elevated Perimeter Risk:  {risk_report['elevated_risk'] * 100:.1f}%")
    print(f"    - Risk Increase Delta:     +{risk_report['risk_increase_percent']:.1f}% ({risk_report['threat_classification']})")

    # 4. GAT Attention and Bridge Detection
    print("\n[Step 4] Running GAT Relational Boundary Detection...")
    detector = AnomalousBridgeDetector(anomaly_threshold=0.6)
    bridges = detector.detect_bridges(injected_graph)
    print(f"[+] Detected {len(bridges)} unauthorized bridgehead(s):")
    for b in bridges:
        print(f"    * Bridge ID: {b['bridge_id']} | Confidence: {b['confidence_score'] * 100:.1f}%")
        print(f"      Insider: {b['insider_name']} <---> Outsider: {b['outsider_name']}")
        print(f"      MITRE Technique: {b['mitre_technique']}")

    # 5. Automated Remediation Plan
    print("\n[Step 5] Assembling SOC Incident Response & Remediation Plan...")
    planner = OutsiderRemediationPlanner()
    plan = planner.build_plan(bridge=bridge_meta, outsider=outsider_meta, baseline_risk=risk_report["elevated_risk"])
    print(f"[+] Plan ID: {plan.plan_id}")
    print("    Operational Defense Actions:")
    for action in plan.actions:
        print(f"      [X] {action.value}")
    print("    MITRE ATT&CK Mitigations:")
    for m in plan.mitre_mitigations:
        print(f"      * {m}")

    # 6. Execute Counterfactual Severance Defense
    print("\n[Step 6] Simulating Counterfactual Bridge Severance (VLAN 999 Isolation)...")
    cf_engine = OutsiderCounterfactualEngine()
    severed_graph, metrics = cf_engine.sever_bridge(
        graph_data=injected_graph,
        insider_idx=insider_idx,
        outsider_idx=injected_graph.num_nodes - 1,
    )
    print(f"[+] Bridge Status: {metrics['status']}")
    print(f"[+] Edges Severed: {metrics['edges_severed']} topological connections zeroed out")
    print(f"[+] Post-Remediation Delta-Risk: {metrics['delta_risk_percent']:.1f}%")
    print("\n[+] Audit Trail Summary:")
    for line in plan.audit_log:
        print(f"    {line}")

    print("\n[+] Demonstration of Insider-Outsider Defense completed successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
