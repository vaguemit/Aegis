"""
Native Local Hypervisor and Host Execution Driver.
Directly interfaces with Windows native subsystem, Hyper-V Host Compute Service (vmcompute),
VMware Workstation Pro CLI (vmrun.exe), and operating system process tables to execute
real-time process termination, network adapter isolation, and virtual machine management
without relying on synthetic mocks.
"""

from typing import Dict, List, Optional, Tuple, Any
import subprocess
import json
import logging
import os
import shutil
import time

logger = logging.getLogger("aegispath.vmware.local_driver")

KNOWN_OFFENSIVE_BINARIES = [
    "chisel", "chisel.exe",
    "ligolo", "ligolo-ng", "ligolo-ng.exe", "agent.exe",
    "nc", "nc.exe", "ncat", "ncat.exe", "socat",
    "cloudflared", "cloudflared.exe",
    "plink", "plink.exe",
    "ngrok", "ngrok.exe",
    "frpc", "frpc.exe",
]


class LocalExecutionDriver:
    """
    Executes real OS-level defense operations:
    1. Real local process enumeration and termination via taskkill/PowerShell.
    2. Real Hyper-V VM discovery and network adapter isolation via PowerShell Direct.
    3. Real VMware Workstation control via vmrun.exe (when installed).
    """

    def __init__(self):
        self.vmrun_path = self._find_vmrun()
        self.hyperv_available = self._check_hyperv()

    def _find_vmrun(self) -> Optional[str]:
        """Locates VMware Workstation CLI tool vmrun.exe if present."""
        candidates = [
            shutil.which("vmrun.exe"),
            r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe",
            r"C:\Program Files\VMware\VMware Workstation\vmrun.exe",
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return None

    def _check_hyperv(self) -> bool:
        """Checks if Hyper-V administration cmdlets are functional on this host."""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Command Get-VM -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "Get-VM" in res.stdout
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns the hardware/hypervisor capabilities detected on this system."""
        return {
            "os": "Windows",
            "hyperv_available": self.hyperv_available,
            "vmware_workstation_available": self.vmrun_path is not None,
            "vmrun_path": self.vmrun_path,
            "can_terminate_local_processes": True,
            "can_isolate_hyperv_adapters": self.hyperv_available,
            "can_control_workstation_vms": self.vmrun_path is not None,
        }

    # ==========================================
    # Real OS Process Management
    # ==========================================

    def list_running_processes(self) -> List[Dict[str, Any]]:
        """
        Queries actual running processes on the operating system using native tasklist.
        Fast, robust, and handles hundreds of processes without PowerShell overhead.
        """
        import csv
        import io
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                reader = csv.reader(io.StringIO(res.stdout))
                procs = []
                for row in reader:
                    if len(row) >= 2:
                        try:
                            pid = int(row[1])
                            procs.append({
                                "pid": pid,
                                "name": row[0],
                                "session": row[2] if len(row) > 2 else "",
                                "mem_usage": row[4] if len(row) > 4 else "",
                                "responding": True,
                            })
                        except ValueError:
                            continue
                return procs
        except Exception as e:
            logger.error(f"Error enumerating local processes via tasklist: {e}")
        return []

    def scan_for_rogue_processes(self) -> List[Dict[str, Any]]:
        """
        Scans real OS processes for known reverse tunnels, C2 agents, and proxies.
        """
        procs = self.list_running_processes()
        rogue = []
        for p in procs:
            name = (p.get("name") or "").lower()
            path = (p.get("path") or "").lower()
            for pattern in KNOWN_OFFENSIVE_BINARIES:
                pat_clean = pattern.replace(".exe", "").lower()
                if name == pat_clean or pattern in path or pat_clean == name:
                    p_copy = dict(p)
                    p_copy["matched_signature"] = pattern
                    rogue.append(p_copy)
                    break
        return rogue

    def terminate_process(self, pid: int) -> Dict[str, Any]:
        """
        Terminates a real process by PID using native taskkill.
        """
        logger.info(f"Executing hard kill on PID {pid}")
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            success = res.returncode == 0
            return {
                "success": success,
                "pid": pid,
                "returncode": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "details": f"Process {pid} forcefully terminated." if success else f"Failed to terminate {pid}: {res.stderr.strip()}",
            }
        except Exception as e:
            logger.error(f"Failed to kill PID {pid}: {e}")
            return {
                "success": False,
                "pid": pid,
                "details": f"Execution error: {str(e)}",
            }

    # ==========================================
    # Real Hyper-V Virtual Machine Management
    # ==========================================

    def list_hyperv_vms(self) -> List[Dict[str, Any]]:
        """Enumerates real virtual machines running on Windows Hyper-V."""
        if not self.hyperv_available:
            return []

        ps_cmd = (
            "Get-VM | Select-Object Name, State, Id, Uptime, "
            "@{N='NetworkAdapters';E={Get-VMNetworkAdapter -VM $_ | Select-Object Name, SwitchName, IPAddresses, MacAddress}} | "
            "ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                return data
        except Exception as e:
            logger.error(f"Error querying Hyper-V: {e}")
        return []

    def quarantine_hyperv_vm(self, vm_name: str, vlan_id: int = 999) -> Dict[str, Any]:
        """
        Isolates a Hyper-V VM by setting its network adapter VLAN to 999 or disconnecting it.
        """
        if not self.hyperv_available:
            return {"success": False, "error": "Hyper-V is not available on this host."}

        # Attempt to isolate via VLAN or disconnection
        ps_cmd = f"""
        $adapter = Get-VMNetworkAdapter -VMName '{vm_name}' -ErrorAction SilentlyContinue
        if ($adapter) {{
            Set-VMNetworkAdapterVlan -VMName '{vm_name}' -Access -VlanId {vlan_id} -ErrorAction SilentlyContinue
            if ($?) {{
                [PSCustomObject]@{{Success=$true; Action='VLAN_MIGRATION'; VlanId={vlan_id}; VM='{vm_name}'}} | ConvertTo-Json
            }} else {{
                Disconnect-VMNetworkAdapter -VMName '{vm_name}' -ErrorAction SilentlyContinue
                [PSCustomObject]@{{Success=$true; Action='VNIC_DISCONNECTED'; VM='{vm_name}'}} | ConvertTo-Json
            }}
        }} else {{
            [PSCustomObject]@{{Success=$false; Error="No VM named '{vm_name}' found."}} | ConvertTo-Json
        }}
        """
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout.strip())
            return {"success": False, "error": res.stderr.strip() or "Command failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # Real VMware Workstation Management
    # ==========================================

    def list_workstation_vms(self) -> List[str]:
        """Lists running VMware Workstation virtual machine .vmx paths."""
        if not self.vmrun_path:
            return []
        try:
            res = subprocess.run(
                [self.vmrun_path, "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0:
                lines = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.startswith("Total running VMs:")]
                return lines
        except Exception as e:
            logger.error(f"vmrun list error: {e}")
        return []

    def quarantine_workstation_vm(self, vmx_path: str) -> Dict[str, Any]:
        """Disconnects virtual Ethernet adapter using vmrun."""
        if not self.vmrun_path:
            return {"success": False, "error": "vmrun.exe not found on system."}
        try:
            res = subprocess.run(
                [self.vmrun_path, "disconnectNamedDevice", vmx_path, "Ethernet0"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return {
                "success": res.returncode == 0,
                "vmx": vmx_path,
                "details": "Disconnected Ethernet0 via vmrun" if res.returncode == 0 else res.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global singleton instance
local_execution_driver = LocalExecutionDriver()
