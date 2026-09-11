# 🛡️ Outsider Node Defense & VMware Production Implementation Architecture

## 1. Executive Summary & Problem Formulation

In enterprise Active Directory (AD) and zero-trust perimeter defense, **outsider nodes** represent unmanaged, unauthorized, or rogue computing assets that are not enrolled in domain inventory or managed by corporate Endpoint Detection and Response (EDR) agents. 

When an **insider node introduces an outsider node**, the enterprise security boundary suffers a **topological perimeter bypass**:

```text
    UNMANAGED EXTERNAL PERIMETER                      MANAGED ENTERPRISE PERIMETER
┌──────────────────────────────────────┐       ┌─────────────────────────────────────────┐
│           OUTSIDER NODE              │       │              INSIDER ASSET              │
│  - Rogue Workstation / BYOD          │       │  - Domain-Joined Workstation            │
│  - Shadow VM (Kali Linux)            │ ◄───► │  - Compromised User Session             │
│  - Covert Reverse SOCKS Proxy        │ Bridge│  - Valid Kerberos TGT Ticket            │
│    (Chisel / Ligolo-ng on Port 1080) │ Link  │  - Internal VLAN 500 Network Adapter    │
└──────────────────────────────────────┘       └───────────────────┬─────────────────────┘
                                                                   │
                                                                   ▼ (Lateral Movement Pivot)
                                               ┌─────────────────────────────────────────┐
                                               │              CROWN JEWELS               │
                                               │  - Primary Domain Controller (DC01)     │
                                               │  - Customer SQL Database Server         │
                                               │  - Active Directory Tier-0 Admin Assets │
                                               └─────────────────────────────────────────┘
```

---

## 2. Threat Vectors: How Insider Nodes Introduce Outsiders

AegisPath models four primary bridgehead mechanisms:

1. **Covert Reverse SOCKS5 Tunneling (`BridgeMechanism.SOCKS_CHISEL_TUNNEL`)**:
   - An adversary executes a lightweight reverse tunneling binary (`chisel.exe`, `ligolo-ng`, `cloudflared`) on an internal workstation.
   - The insider initiates an outbound connection (often over HTTPS port 443) to an external C2 server, establishing a multiplexed TCP tunnel that exposes corporate subnets back to external actors.
   - **MITRE ATT&CK**: `T1090` (Proxy), `T1572` (Protocol Tunneling).

2. **Physical & Network Tethering (`BridgeMechanism.DUAL_HOMED_NIC`)**:
   - An insider connects a secondary network interface (USB Ethernet dongle, mobile hotspot WiFi adapter) to an external network while staying attached to the corporate LAN.
   - The insider OS acts as a router/bridge between trusted and untrusted networks.
   - **MITRE ATT&CK**: `T1200` (Hardware Additions), `T1021` (Remote Services).

3. **Hypervisor Shadow IT & Rogue Guest Injection (`BridgeMechanism.VMWARE_SHARED_NAT`)**:
   - An unauthorized virtual machine (e.g. Kali Linux, Docker container) is spawned locally on an ESXi host or desktop hypervisor using NAT or bridged virtual networking.
   - **MITRE ATT&CK**: `T1584` (Compromise Infrastructure).

4. **Credential & Token Delegation Pivoting (`BridgeMechanism.CREDENTIAL_DELEGATION`)**:
   - Leaked Kerberos tickets, NTLM hashes, or OAuth refresh tokens are shared with an unmanaged external system.
   - **MITRE ATT&CK**: `T1558` (Steal or Forge Kerberos Tickets), `T1078` (Valid Accounts).

---

## 3. AegisPath's Graph Learning & Topological Defense

When an outsider node is introduced, AegisPath executes a four-phase response:

### Phase 1: Inductive Graph Representation & Dynamic Tensor Expansion
- Standard static graph models fail on unseen nodes. AegisPath utilizes **Inductive Graph Attention Networks (GAT)** with dynamic tensor expansion:
  $$\mathbf{X} \in \mathbb{R}^{N \times 20} \longrightarrow \mathbf{X}' \in \mathbb{R}^{(N+1) \times 20}$$
  $$\mathbf{A} \in \mathbb{R}^{N \times N \times 16} \longrightarrow \mathbf{A}' \in \mathbb{R}^{(N+1) \times (N+1) \times 16}$$
- The outsider node feature vector encodes:
  - Entity Type: `COMPUTER`
  - Flags: `IS_VULNERABLE = 1`, `OWNED = 1` (foothold)
  - Operating System: `OTHER_LINUX` or Unmanaged
  - Metadata: Non-domain MAC address, isolated VLAN ID

### Phase 2: Boundary-Crossing Attention Bottleneck Detection
- AegisPath's `AnomalousBridgeDetector` inspects cross-perimeter attention weights ($\alpha_{u, v}$):
  $$\text{Confidence}(u, v) = \sigma\left(\mathbf{W}_{\text{boundary}} \cdot [\alpha_{u, v} \,\|\, \mathbf{h}_u \,\|\, \mathbf{h}_v] + \beta_{\text{anomaly}}\right)$$
- Identifies internal assets communicating with unmanaged endpoints over high-risk administrative channels (`AdminTo`, `ExecuteDCOM`, `CanRDP`, `Open`).

### Phase 3: Exact Risk Elevation Scoring
- Evaluates the security posture delta:
  $$\Delta\text{Risk}_{\text{introduced}} = \text{Risk}(\mathcal{G}_{\text{with outsider}}) - \text{Risk}(\mathcal{G}_{\text{baseline}})$$
- If the insider is a high-value or Tier-0 asset, the risk increase triggers an immediate automated SOC incident escalation (`CRITICAL_PERIMETER_BYPASS`).

### Phase 4: Automated Counterfactual Severance Defense
- **Bridge Severance**: Zeroes out relational adjacency channels between insider and outsider without disrupting internal business operations:
  $$\mathbf{A}'[u_{\text{insider}}, v_{\text{outsider}}, :] = \mathbf{0}, \quad \mathbf{A}'[v_{\text{outsider}}, u_{\text{insider}}, :] = \mathbf{0}$$
- **Hypervisor Network Quarantine**: Moves the vNIC backing to `Quarantine_VLAN_999`.
- **In-Guest Process Termination**: Leverages VMware Tools Guest Operations bus to kill the reverse proxy process (`chisel.exe`) at the hypervisor level.
- Computes counterfactual risk reduction: $\Delta\text{Risk} = -100\%$.

---

## 4. VMware vSphere Production Implementation Suite

AegisPath includes a complete, production-grade VMware integration package (`src/vmware/`):

| Module | Purpose & Core Class |
|---|---|
| `src/vmware/client.py` | `VMwareClient`: REST session authentication (`POST /api/session`) with automatic fallback to high-fidelity emulation. |
| `src/vmware/discovery.py` | `VMwareTopologyDiscoverer`: Enumerates ESXi bare-metal hosts, hardware specs, and virtual machines. |
| `src/vmware/network_mapper.py` | `VMwareNetworkMapper`: Maps standard and distributed vSwitches, Portgroups, and VLAN distributions. |
| `src/vmware/rogue_detector.py` | `VMwareRogueDetector`: Scans for non-domain joined VMs, offensive security distros (Kali), and promiscuous vNICs. |
| `src/vmware/bridge_detector.py` | `VMwareBridgeDetector`: Detects dual-homed VMs bridging internal VLANs to external DMZ networks. |
| `src/vmware/security_auditor.py` | `VMwareSecurityAuditor`: Audits promiscuous mode, MAC address changes, and forged transmit policies. |
| `src/vmware/quarantine.py` | `VMwareActiveQuarantine`: Migrates vNIC to `Quarantine_VLAN_999`, disconnects virtual Ethernet adapters, or powers off VMs. |
| `src/vmware/forensics.py` | `VMwareForensicManager`: Captures immutable pre-isolation snapshots with volatile RAM memory dumps. |
| `src/vmware/guest_ops.py` | `VMwareGuestOpsManager`: In-guest process inspection and automated termination of reverse tunnel binaries via VMware Tools. |
| `src/vmware/telemetry.py` | `VMwareTelemetryStreamer`: RFC 5424 compliant Syslog streaming and hypervisor audit ring-buffer. |
| `src/vmware/graph_sync.py` | `VMwareGraphSynchronizer`: Maps live vSphere cluster into AegisPath Active Directory graph tensors. |

---

## 5. Verification and CLI Execution

### 1. Run Live VMware Cluster Synchronization:
```bash
python scripts/vmware_live_sync.py --host vcenter.corp.internal --emulate
```

### 2. Run Interactive Insider-Outsider Threat Demonstration:
```bash
python scripts/demo_outsider_bridge.py
```

### 3. Run VMware Hypervisor Active Defense & Memory Snapshot Demo:
```bash
python scripts/vmware_quarantine_demo.py
```

### 4. Execute Complete Automated Test Suites:
```bash
pytest tests/test_outsider_defense.py tests/test_vmware_integration.py tests/test_vmware_api.py tests/test_outsiders_api.py
```
