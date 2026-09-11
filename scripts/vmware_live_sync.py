"""
VMware Live Infrastructure Graph Synchronizer CLI.
Connects to VMware vCenter or standalone ESXi hypervisor, enumerates cluster inventory,
audits network security policies, and synchronizes the live topology into AegisPath.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vmware.config import VMwareConfig
from src.vmware.client import VMwareClient
from src.vmware.discovery import VMwareTopologyDiscoverer
from src.vmware.network_mapper import VMwareNetworkMapper
from src.vmware.rogue_detector import VMwareRogueDetector
from src.vmware.graph_sync import VMwareGraphSynchronizer


def main():
    parser = argparse.ArgumentParser(description="AegisPath VMware Live Infrastructure Synchronizer")
    parser.add_argument("--host", default="vcenter.corp.internal", help="vCenter / ESXi hostname or IP")
    parser.add_argument("--user", default="administrator@vsphere.local", help="vSphere Username")
    parser.add_argument("--password", default="VMwareSecretPass!2026", help="vSphere Password")
    parser.add_argument("--port", type=int, default=443, help="HTTPS port")
    parser.add_argument("--no-verify-ssl", action="store_true", default=True, help="Disable SSL certificate check")
    parser.add_argument("--emulate", action="store_true", default=True, help="Enable fallback emulation mode")
    args = parser.parse_args()

    print("=" * 70)
    print("[AegisPath] VMware vSphere Live Synchronization Engine")
    print("=" * 70)

    cfg = VMwareConfig(
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        verify_ssl=not args.no_verify_ssl,
        enable_emulation_fallback=args.emulate,
    )

    client = VMwareClient(cfg)
    print(f"[*] Connecting to VMware vCenter at {args.host}:{args.port}...")
    if not client.connect():
        print("[-] Failed to establish connection to vCenter. Exiting.")
        sys.exit(1)

    print(f"[+] Connected successfully (Emulated mode: {client.is_emulated})")
    print(f"[+] Session Token: {client.session_id}")

    # 1. Discover Inventory
    print("\n[*] Enumerating cluster hardware and virtual machines...")
    discoverer = VMwareTopologyDiscoverer(client)
    report = discoverer.discover_cluster()
    print(f"[+] Discovered {report.total_hosts} physical ESXi hosts and {report.total_vms} virtual machines.")

    for h in report.hosts:
        print(f"    - Host: {h.name} ({h.esxi_version}) | IP: {h.management_ip}")

    # 2. Network Topology
    print("\n[*] Mapping vSwitch topology and VLAN distribution...")
    mapper = VMwareNetworkMapper(client)
    topo = mapper.get_network_topology()
    for sw in topo["vswitches"]:
        print(f"    - vSwitch: {sw['name']} ({sw['type']}, Uplinks: {sw['uplinks']})")
    for pg, details in topo["portgroups"].items():
        print(f"      * Portgroup: {pg} (VLAN {details['vlan_id']}) -> {details['vm_count']} VMs connected")

    # 3. Rogue Outsider Detection
    print("\n[*] Scanning for rogue outsider VMs and shadow IT...")
    detector = VMwareRogueDetector(client)
    rogue_vms = detector.scan_for_rogue_vms()
    if rogue_vms:
        print(f"[!] ALERT: Found {len(rogue_vms)} unmanaged outsider VMs:")
        for r in rogue_vms:
            print(f"    - [CRITICAL] {r['vm_name']} (IP: {r['ip_address']}, OS: {r['guest_os']})")
            print(f"      Threat Confidence: {r['threat_confidence'] * 100:.1f}% | Action: {r['recommended_action']}")
    else:
        print("[+] No rogue outsider VMs detected. Perimeter intact.")

    # 4. Graph Synchronization
    print("\n[*] Converting VMware cluster into AegisPath Active Directory Graph...")
    syncer = VMwareGraphSynchronizer(client)
    graph_data = syncer.sync_to_graph_data()
    print(f"[+] Generated Graph: {graph_data.graph_id}")
    print(f"[+] Total Nodes: {graph_data.num_nodes} (Feature Dim: {graph_data.x_matrix.shape[1]})")
    print(f"[+] Total Relational Edges: {int((graph_data.adj_tensor > 0).sum().item())}")
    print(f"[+] Crown Jewel Target: {graph_data.node_names[graph_data.target_idx]}")
    print("\n[+] Live VMware synchronization completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
