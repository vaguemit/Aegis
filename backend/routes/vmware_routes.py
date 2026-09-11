"""
VMware vSphere & ESXi Hypervisor Management API Endpoints.
Provides REST routes for inventory discovery, rogue VM detection, active defense quarantine,
forensic memory snapshots, guest operations process management, and live graph synchronization.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.vmware.config import VMwareConfig
from src.vmware.client import VMwareClient
from src.vmware.discovery import VMwareTopologyDiscoverer
from src.vmware.vm_manager import VMwareVMManager
from src.vmware.network_mapper import VMwareNetworkMapper
from src.vmware.security_auditor import VMwareSecurityAuditor
from src.vmware.rogue_detector import VMwareRogueDetector
from src.vmware.bridge_detector import VMwareBridgeDetector
from src.vmware.quarantine import VMwareActiveQuarantine
from src.vmware.forensics import VMwareForensicManager
from src.vmware.guest_ops import VMwareGuestOpsManager
from src.vmware.telemetry import VMwareTelemetryStreamer
from src.vmware.graph_sync import VMwareGraphSynchronizer
from src.vmware.models import QuarantineMethod
from backend.graph_manager import graph_manager

router = APIRouter(prefix="/api/vmware", tags=["vmware"])

# Shared singleton client and telemetry streamer
vmware_config = VMwareConfig.from_env()
vmware_client = VMwareClient(vmware_config)
vmware_client.connect()
vmware_streamer = VMwareTelemetryStreamer()


# Pydantic Schemas
class VMwareConnectRequest(BaseModel):
    host: Optional[str] = "vcenter.corp.internal"
    port: Optional[int] = 443
    username: Optional[str] = "administrator@vsphere.local"
    password: Optional[str] = "VMwareSecretPass!2026"
    verify_ssl: Optional[bool] = False
    enable_emulation: Optional[bool] = True


class QuarantineRequest(BaseModel):
    vm_id: str = Field(..., description="VM ID or VM display name")
    method: str = Field("PORTGROUP_MIGRATION", description="PORTGROUP_MIGRATION | VNIC_DISCONNECT | POWER_OFF")
    quarantine_portgroup: Optional[str] = "Quarantine_VLAN_999"


class RestoreRequest(BaseModel):
    vm_id: str
    target_portgroup: str = "Workstations-VLAN500"
    vlan_id: int = 500


class SnapshotRequest(BaseModel):
    vm_id: str
    snapshot_name: Optional[str] = None
    include_memory: bool = True


class TerminateProcessRequest(BaseModel):
    vm_id: str
    pid: Optional[int] = None


@router.get("/status")
def get_vmware_status() -> Dict[str, Any]:
    """Returns connectivity and session health for VMware vCenter / ESXi."""
    return vmware_client.get_status()


@router.post("/connect")
def connect_vmware(req: VMwareConnectRequest) -> Dict[str, Any]:
    """Establishes authenticated session with VMware vCenter."""
    vmware_client.config.host = req.host or vmware_client.config.host
    vmware_client.config.port = req.port or vmware_client.config.port
    vmware_client.config.username = req.username or vmware_client.config.username
    vmware_client.config.password = req.password or vmware_client.config.password
    vmware_client.config.verify_ssl = req.verify_ssl if req.verify_ssl is not None else vmware_client.config.verify_ssl
    vmware_client.config.enable_emulation_fallback = req.enable_emulation if req.enable_emulation is not None else True

    vmware_client.disconnect()
    success = vmware_client.connect()
    return {
        "success": success,
        "status": vmware_client.get_status(),
    }


@router.get("/inventory")
def get_inventory() -> Dict[str, Any]:
    """Retrieves full cluster inventory including ESXi hosts and virtual machines."""
    discoverer = VMwareTopologyDiscoverer(vmware_client)
    report = discoverer.discover_cluster()
    return {
        "cluster_name": report.cluster_name,
        "vcenter_host": report.vcenter_host,
        "total_hosts": report.total_hosts,
        "total_vms": report.total_vms,
        "total_vswitches": report.total_vswitches,
        "hosts": [
            {
                "host_id": h.host_id,
                "name": h.name,
                "version": h.esxi_version,
                "management_ip": h.management_ip,
                "memory_gb": round(h.total_memory_mb / 1024, 1),
                "cpu_cores": h.total_cpu_mhz // 2400,
                "vm_count": len(h.vm_ids),
                "state": h.state,
            }
            for h in report.hosts
        ],
        "vms": [
            {
                "vm_id": vm.vm_id,
                "name": vm.name,
                "power_state": vm.power_state.value,
                "guest_os": vm.guest_os,
                "ip_address": vm.ip_address,
                "cpu_count": vm.cpu_count,
                "memory_mb": vm.memory_mb,
                "is_outsider": vm.is_outsider,
                "is_isolated": vm.is_isolated,
                "portgroup": vm.nics[0].portgroup if vm.nics else "None",
                "vlan_id": vm.nics[0].vlan_id if vm.nics else 0,
            }
            for vm in report.vms
        ],
        "discovered_at": report.discovered_at,
    }


@router.get("/network-topology")
def get_network_topology() -> Dict[str, Any]:
    """Maps virtual switch configurations, portgroups, and VLAN distribution."""
    mapper = VMwareNetworkMapper(vmware_client)
    return mapper.get_network_topology()


@router.get("/rogue-vms")
def get_rogue_vms() -> List[Dict[str, Any]]:
    """Scans for unmanaged outsider virtual machines and shadow IT."""
    detector = VMwareRogueDetector(vmware_client)
    return detector.scan_for_rogue_vms()


@router.get("/audit-security")
def audit_security() -> Dict[str, Any]:
    """Audits vSwitch L2 security policies (promiscuous mode, MAC changes)."""
    auditor = VMwareSecurityAuditor(vmware_client)
    return auditor.audit_security_policies()


@router.post("/quarantine")
def quarantine_vm(req: QuarantineRequest) -> Dict[str, Any]:
    """Executes hypervisor-level network quarantine on a virtual machine."""
    quarantine = VMwareActiveQuarantine(vmware_client, vmware_streamer)
    method_enum = QuarantineMethod(req.method) if req.method in QuarantineMethod.__members__ else QuarantineMethod.PORTGROUP_MIGRATION
    res = quarantine.quarantine_vm(
        vm_id=req.vm_id,
        quarantine_portgroup=req.quarantine_portgroup,
        method=method_enum,
    )
    return {
        "success": res.success,
        "action_id": res.action_id,
        "vm_id": res.vm_id,
        "vm_name": res.vm_name,
        "method": res.method.value,
        "details": res.details,
        "new_state": res.new_state,
        "timestamp": res.timestamp,
    }


@router.post("/restore")
def restore_vm(req: RestoreRequest) -> Dict[str, Any]:
    """Restores a quarantined VM back to a production portgroup."""
    quarantine = VMwareActiveQuarantine(vmware_client, vmware_streamer)
    res = quarantine.restore_vm_network(
        vm_id=req.vm_id,
        target_portgroup=req.target_portgroup,
        vlan_id=req.vlan_id,
    )
    return {
        "success": res.success,
        "action_id": res.action_id,
        "vm_name": res.vm_name,
        "details": res.details,
    }


@router.post("/snapshot")
def capture_snapshot(req: SnapshotRequest) -> Dict[str, Any]:
    """Captures pre-isolation forensic snapshot and memory dump."""
    forensics = VMwareForensicManager(vmware_client, vmware_streamer)
    snap = forensics.capture_forensic_snapshot(
        vm_id=req.vm_id,
        snapshot_name=req.snapshot_name,
        include_memory=req.include_memory,
    )
    return {
        "success": True,
        "snapshot_id": snap.snapshot_id,
        "vm_name": snap.vm_name,
        "name": snap.name,
        "memory_dump_included": snap.memory_dump_included,
        "file_path": snap.file_path,
        "timestamp": snap.timestamp,
    }


@router.get("/guest-ops/processes")
def list_guest_processes(vm_id: str = Query(..., description="VM ID or name")) -> Dict[str, Any]:
    """Lists processes running inside guest OS and flags rogue binaries."""
    guest_ops = VMwareGuestOpsManager(vmware_client)
    procs = guest_ops.list_guest_processes(vm_id)
    rogue = guest_ops.find_rogue_processes(vm_id)
    return {
        "vm_id": vm_id,
        "total_processes": len(procs),
        "rogue_processes_count": len(rogue),
        "processes": [
            {
                "pid": p.pid,
                "name": p.name,
                "cmdline": p.cmdline,
                "owner": p.owner,
                "start_time": p.start_time,
                "is_rogue": p.is_rogue,
            }
            for p in procs
        ],
    }


@router.post("/guest-ops/terminate-rogue")
def terminate_rogue_processes(req: TerminateProcessRequest) -> Dict[str, Any]:
    """Terminates rogue reverse proxy/tunnel processes via Guest Operations bus."""
    guest_ops = VMwareGuestOpsManager(vmware_client)
    if req.pid:
        res = guest_ops.terminate_guest_process(req.vm_id, req.pid)
        return res
    else:
        res = guest_ops.terminate_all_rogue_processes(req.vm_id)
        return res


@router.post("/sync-graph")
def sync_vmware_graph() -> Dict[str, Any]:
    """Synchronizes live VMware cluster topology into active AegisPath graph."""
    syncer = VMwareGraphSynchronizer(vmware_client)
    graph_data = syncer.sync_to_graph_data()
    # Store into graph_manager
    graph_manager.set_graph(graph_data)
    return {
        "success": True,
        "graph_id": graph_data.graph_id,
        "num_nodes": graph_data.num_nodes,
        "source_node": graph_data.node_names[graph_data.source_idx] if graph_data.node_names else f"node_{graph_data.source_idx}",
        "target_node": graph_data.node_names[graph_data.target_idx] if graph_data.node_names else f"node_{graph_data.target_idx}",
        "message": f"Successfully mapped {graph_data.num_nodes} VMware instances into AegisPath Active Directory graph.",
    }


@router.get("/events")
def get_events(limit: int = Query(25, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Retrieves live hypervisor audit and Syslog events."""
    return vmware_streamer.get_recent_events(limit=limit)
