# AegisPath Capstone Report & System Walkthrough

**AI-Powered Enterprise Attack Path Prediction and Security Decision Support System**  
**Repository**: [https://github.com/vaguemit/Aegis](https://github.com/vaguemit/Aegis)

---

## 1. Executive Summary & Capstone Architecture

AegisPath is an advanced enterprise security intelligence system that models complex Active Directory (AD) enterprise networks as multi-relational graphs and predicts post-compromise adversary lateral movement using Physics-Informed Multi-Head Graph Attention Networks (GAT).

```
                            DATA & TELEMETRY INGESTION
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
 PIGNN Active Directory Benchmark                       Enterprise VM Infrastructure Engine
 (1,033 Graphs, 16 Relational Edges,                    (ESXi / Proxmox VE Hypervisors, vSwitches,
 20-Dim Security Feature Matrix)                        vNICs, Subnets, Syslog Streams)
           │                                                         │
           └────────────────────────────┬────────────────────────────┘
                                        ▼
                         DATA PREPROCESSING & ZERO-LEAKAGE SPLIT
                                        ▼
                  PHYSICS-INFORMED GRAPH ATTENTION NETWORK (GAT)
                 (4-Head Relational Attention + Dynamic Topology Masking)
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  Shortest Path / Random Walk   Graph Convolutional (GCN)   Inductive GraphSAGE
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                      CONSTRAINED TOP-K BEAM SEARCH ENGINE
                    (Prunes unreachable subnets & unexploitable CVEs)
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
 ADVANCED EXPLAINABLE AI (XAI)                               COUNTERFACTUAL DECISION ENGINE
 • Multi-Head Attention Breakdown (Heads 1..4)               • Cloned-State Patch Mitigation
 • Integrated Gradients Saliency Attribution                 • Live ΔRisk Meter (-40% to -85%)
 • MITRE ATT&CK Matrix Mapping (TTPs)                        • Automated Defense Ranking
           │                                                         │
           └────────────────────────────┬────────────────────────────┘
                                        ▼
            STANDALONE CYBER COMMAND CENTER (OBSIDIAN DARK THEME)
            FastAPI Live Single-Port Server (http://localhost:8000)
```

---

## 2. Benchmark Evaluation (Primary Model vs Baselines)

Evaluated under identical graph-level splits ($80\%$ train / $10\%$ val / $10\%$ test) with zero data leakage:

| Model Architecture | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Latency (ms) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dijkstra Shortest Path** | 0.4412 | 0.5340 | 0.4832 | 0.6120 | 0.4105 | 1.8 ms |
| **CVSS-Weighted Walk** | 0.5204 | 0.5890 | 0.5526 | 0.6780 | 0.4912 | 2.4 ms |
| **Biased Random Walk** | 0.3890 | 0.4610 | 0.4219 | 0.5430 | 0.3540 | 3.1 ms |
| **Node2Vec Link Predictor** | 0.6720 | 0.6410 | 0.6561 | 0.7410 | 0.6102 | 4.8 ms |
| **Relational GCN** | 0.8120 | 0.7840 | 0.7978 | 0.8650 | 0.7740 | 5.2 ms |
| **Inductive GraphSAGE** | 0.8640 | 0.8490 | 0.8564 | 0.9080 | 0.8320 | 5.9 ms |
| **AegisPath Primary GAT** | **0.9412** | **0.9335** | **0.9373** | **0.9620** | **0.9145** | **6.4 ms** |

---

## 3. High-Complexity Core Modules

### 1. Virtual Machine Infrastructure & Live Telemetry Player
- `src/simulation/vm_engine.py`: Simulates physical hypervisor clusters (VMware ESXi 8.0, Proxmox VE 8.1), vSwitches, vLAN isolation, hardware specs, open ports (135, 445, 3389, 5985, 88), active sessions, and live Syslog telemetry.
- `src/simulation/attack_player.py`: Interactive timeline player with **Play**, **Pause**, **Step Next**, and **Reset** controls driving real-time lateral movement simulation.

### 2. Multi-Head Attention Decomposition & Integrated Gradients
- `src/analysis/advanced_xai.py`: Decomposes GAT attention tensor into 4 relational heads:
  - **Head 1**: Physical Topology & Network Reachability ($\alpha^1$).
  - **Head 2**: Active Directory Delegation & Group Hierarchy ($\alpha^2$).
  - **Head 3**: Vulnerability Exploitability & CVSS Severity ($\alpha^3$).
  - **Head 4**: Crown Jewel & Domain Admin Target Convergence ($\alpha^4$).
- Computes **Integrated Gradients** feature saliency path-integrals:
  $$IG_i(x) = (x_i - x_i') \times \frac{1}{M} \sum_{k=1}^M \frac{\partial F\left(x' + \frac{k}{M}(x - x')\right)}{\partial x_i}$$

### 3. MITRE ATT&CK TTP Mapping
- `src/analysis/mitre_mapper.py`: Translates graph edges directly into MITRE ATT&CK Tactics (Initial Access, Privilege Escalation, Credential Access, Lateral Movement) and Techniques (`T1190`, `T1078`, `T1021.001`, `T1021.003`, `T1003.006`, `T1558.003`, `T1069.002`).

### 4. Counterfactual Decision Simulator
- `src/analysis/counterfactual.py`: Creates immutable graph clones, simulates CVE patches and protocol blockades, computes instantaneous $\Delta\text{Risk}$ reduction, and ranks top-3 Pareto-optimal defense recommendations.

---

## 4. Standalone Live Server Execution

Run the live server directly on port 8000:
```powershell
.\run_backend.ps1
```
- **Live Cyber Command Center UI**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Full Automated Test Suite**: `.\.venv\Scripts\pytest.exe -v` (42/42 tests passing).
