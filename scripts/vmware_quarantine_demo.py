"""
VMware Hypervisor Active Defense & In-Guest Quarantine Demonstration CLI.
Demonstrates automated forensic memory snapshot dumping, guest process termination,
and hypervisor vNIC portgroup quarantine for compromised assets.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vmware.config import VMwareConfig
from src.vmware.client import VMwareClient
from src.vmware.vm_manager import VMwareVMManager
from src.vmware.rogue_detector import VMwareRogueDetector
from src.vmware.forensics import VMwareForensicManager
from src.vmware.guest_ops import VMwareGuestOpsManager
from src.vmware.quarantine import VMwareActiveQuarantine
from src.vmware.models import QuarantineMethod


def main():
    print("=" * 72)
    print("[AegisPath] VMware vSphere Hypervisor Active Defense Automation")
    print("=" * 72)

    cfg = VMwareConfig(enable_emulation_fallback=True)
    client = VMwareClient(cfg)
    client.connect()

    print(f"\n[Step 1] Connected to vCenter Cluster ({client.config.cluster})")
    print(f"[+] Status: Authenticated | Session: {client.session_id}")

    # 1. Detect Rogue Outsider VM
    print("\n[Step 2] Scanning Cluster for Rogue Outsider Assets...")
    detector = VMwareRogueDetector(client)
    findings = detector.scan_for_rogue_vms()
    if not findings:
        print("[-] No rogue VMs found. Selecting default target VM-WS01.")
        target_vm_name = "VM-WS01"
    else:
        target_vm_name = findings[0]["vm_name"]
        print(f"[!] Threat Detected: '{target_vm_name}' (Threat Confidence: {findings[0]['threat_confidence']*100:.1f}%)")
        for r in findings[0]["risk_indicators"]:
            print(f"    - {r}")

    # 2. Inspect In-Guest Processes via VMware Tools
    print(f"\n[Step 3] Querying In-Guest Operating System Processes via VMware Tools...")
    guest_ops = VMwareGuestOpsManager(client)
    procs = guest_ops.list_guest_processes(target_vm_name)
    rogue_procs = guest_ops.find_rogue_processes(target_vm_name)
    print(f"[+] Found {len(procs)} active processes inside {target_vm_name}.")
    for rp in rogue_procs:
        print(f"    [!] Malicious Process: PID {rp.pid} | {rp.name} | Owner: {rp.owner}")
        print(f"        Cmd: {rp.cmdline}")

    # 3. Capture Pre-Isolation Forensic Snapshot with RAM Dump
    print(f"\n[Step 4] Capturing Digital Forensic Snapshot & Dumping Volatile RAM...")
    forensics = VMwareForensicManager(client)
    snap = forensics.capture_forensic_snapshot(target_vm_name, include_memory=True)
    print(f"[+] Forensic Snapshot Created: {snap.snapshot_id}")
    print(f"    - Snapshot Label: {snap.name}")
    print(f"    - Volatile RAM Dump: {snap.memory_dump_included} (Preserved for digital forensics)")
    print(f"    - Storage Backing: {snap.file_path}")

    # 4. Terminate In-Guest C2 Reverse Tunnel
    print(f"\n[Step 5] Terminating Malicious In-Guest Processes via Guest Operations...")
    term_result = guest_ops.terminate_all_rogue_processes(target_vm_name)
    print(f"[+] Terminated {term_result['terminated_count']} rogue process(es) inside guest OS:")
    for t in term_result["terminated"]:
        print(f"    * PID {t['pid']} ({t['name']}) -> Terminated")

    # 5. Hypervisor-Level Network Quarantine
    print(f"\n[Step 6] Enforcing Hypervisor-Level Network Quarantine (VLAN 999)...")
    quarantine = VMwareActiveQuarantine(client)
    q_res = quarantine.quarantine_vm(target_vm_name, method=QuarantineMethod.PORTGROUP_MIGRATION)
    print(f"[+] Quarantine Action: {q_res.action_id}")
    print(f"[+] Target VM: {q_res.vm_name}")
    print(f"[+] Enforcement Method: {q_res.method.value}")
    print(f"[+] Status: {q_res.details}")
    print(f"    - Previous State: {q_res.previous_state}")
    print(f"    - New State:      {q_res.new_state}")

    print("\n[+] VMware Active Defense incident response automation completed successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
