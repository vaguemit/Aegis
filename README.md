# 🛡️ AegisPath: Explainable Graph Attention Neural Network (GAT) for Enterprise Attack Path Forecasting & Counterfactual Defense

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![Cytoscape.js](https://img.shields.io/badge/Cytoscape.js-3.28-FF6B6B.svg)](https://js.cytoscape.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20v14-orange.svg)](https://attack.mitre.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AegisPath** is a research-grade, explainable graph learning system designed for proactive cyber risk assessment, multi-hop lateral movement prediction, and real-time counterfactual defense simulation in enterprise Active Directory (AD) environments.

Rather than assessing vulnerabilities in isolation or computing naive static reachability graphs, AegisPath leverages **Relational Multi-Head Graph Attention Networks (GAT)** trained on **1,033 enterprise network topologies** to forecast probable adversary trajectories, deliver multi-perspective **eXplainable AI (XAI)** attributions with **MITRE ATT&CK** mappings, and simulate defensive remediations with exact risk reduction calculations ($\Delta\text{Risk}$).

---

## 🏛️ System Architecture

```text
                                  ENTERPRISE DATA SOURCES
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
             Active Directory Benchmark                    Synthetic Generator
              (1,033 Empirical Graphs)                   (15 - 500 Custom Nodes)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                HETEROGENEOUS GRAPH ENCODING
                       ┌───────────────────────────────────────────┐
                       │  - 20-dim Entity & Security Features (X)  │
                       │  - 16-channel Relational Adjacency (A)    │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                 GRAPH ATTENTION NETWORK (GAT)
                       ┌───────────────────────────────────────────┐
                       │  - 4-Head Relational Graph Attention      │
                       │  - Scaled Bilinear Dot-Product Scoring    │
                       │  - Physics Constraints (Degree & Cycle)   │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                DIVERSE CONSTRAINED BEAM SEARCH
                       ┌───────────────────────────────────────────┐
                       │  - Security Precondition Verification     │
                       │  - Multi-Vector Diverse Path Exploration  │
                       │  - Top-K Feasible Trajectories            │
                       └─────────────────────┬─────────────────────┘
                                             │
         ┌──────────────────────────┬────────┴──────────────────────────┬──────────────────────────┐
         ▼                          ▼                                   ▼                          ▼
  [ XAI ATTRIBUTION ]    [ MITRE ATT&CK ENGINE ]            [ COUNTERFACTUAL ENGINE ]    [ VM INFRASTRUCTURE ]
  - 4-Head Attention      - Technique Mapping (T1190, etc.)   - CVE Patch Simulation      - ESXi / Proxmox Hosts
  - Integrated Gradients  - Tactic ID & Defense Recs          - Service Port Blockades    - vSwitch & Port Maps
  - Saliency Subgraphs    - Security Team Guidance            - Real-Time Delta Risk      - Live Syslog Telemetry
```

---

## 🔬 Key Capabilities & Innovations

### 1. Multi-Head Relational Graph Attention Network (GAT)
- Implements custom multi-head attention layers with relational edge biases across 16 Active Directory relationship types (`AdminTo`, `CanRDP`, `ExecuteDCOM`, `GenericAll`, `DCSync`, etc.).
- Utilizes high-throughput **scaled bilinear dot-product prediction heads** operating at $<1.5\text{ms}$ latency per graph.

### 2. Physics-Informed Regularization Losses
- **Focal Edge Loss**: Addresses extreme topological class imbalance ($\sim 1:250$).
- **Degree Penalty Loss**: Prevents physically impossible branching behaviors.
- **Cycle Suppression Loss**: Penalizes cyclic attacker loops via trace-matrix powers $\operatorname{Tr}(\mathbf{P}^k)$.

### 3. Diverse Feasibility-Constrained Beam Search
- Explores multiple distinct lateral movement vectors (e.g., Web Server CVE Exploit vs. Kerberoasting vs. RDP pivot) while verifying that every hop satisfies security preconditions and token permissions.

### 4. Advanced XAI & MITRE ATT&CK Attribution
- **Multi-Head Attention Decomposition**: Inspects individual head weights across semantic relationships.
- **Integrated Gradients (Path-Integral Saliency)**: Calculates exact feature attributions ($\frac{\partial P}{\partial x}$) for node features like unpatched CVEs, Kerberoastable SPNs, and high-privilege memberships.
- **MITRE ATT&CK Engine**: Automatically tags edges with MITRE Tactics (`TA0001` Initial Access, `TA0008` Lateral Movement, `TA0006` Credential Access) and Techniques (`T1190`, `T1078`, `T1021.001`, `T1003.006`, `T1558.003`).

### 5. Counterfactual Defense & Decision Support
- Dynamically clones graph states to simulate **Vulnerability Patching**, **Protocol Disablement (SMB/RDP/DCOM)**, and **Privilege Revocation**.
- Computes exact $\Delta\text{Risk}$ metrics, verifying whether an attack path is completely severed (**-100% Risk**) or diverted through a secondary route.

### 6. Full Virtual Machine Infrastructure Emulation
- Synthesizes realistic hypervisors (**VMware ESXi 8.0**, **Proxmox VE 8.1**, **Hyper-V**), virtual switches, vNIC MAC addresses, open service ports (`135`, `445`, `3389`, `5985`, `88`), active user logon sessions, and real-time Syslog telemetry.

### 7. Obsidian Command Center Dashboard
- **Hierarchical Tiered View**: Organizes topologies into clean layers (Domain Controllers $\to$ Production Servers $\to$ Workstations).
- **Concentric Security Rings**: Displays defense-in-depth perimeters with crown jewels at the center.
- **Dynamic Origin & Target Picker**: Select any starting machine and any crown jewel destination with 1 click.
- **Live Attack Timeline Player**: Step-by-step playback with synchronized terminal audit events.

---

## 📊 Dataset & Mathematical Schema

Each enterprise environment $\mathcal{G}$ is represented as:

$$\mathcal{G} = (\mathbf{X}, \mathbf{A}, \mathbf{Y})$$

### 1. Node Feature Matrix ($\mathbf{X} \in \mathbb{R}^{N \times 20}$)
Contains 20 one-hot and boolean security attributes:
- **Entity Type (6-dim one-hot)**: `Domain`, `DomainController`, `Computer`, `User`, `Group`, `OU`, `GPO`.
- **Operating System (7-dim one-hot)**: `Win10`, `Win7`, `WinServer2016_2019`, `WinServer2012`, `WinServer2008`, `Linux`, `Other`.
- **Security Flags (7-dim boolean)**: `enabled`, `hasspn`, `highvalue`, `is_vulnerable`, `is_target`, `is_owned`, `admin_rights`.

### 2. Relational Adjacency Tensor ($\mathbf{A} \in \mathbb{R}^{N \times N \times 16}$)
Encodes 16 directed Active Directory permission and communication channels:
`AdminTo`, `AllowedToDelegate`, `CanRDP`, `Contains`, `DCSync`, `ExecuteDCOM`, `GenericAll`, `GetChanges`, `GetChangesAll`, `GpLink`, `HasSession`, `MemberOf`, `Open`, `Owns`, `WriteDacl`, `WriteOwner`.

### 3. Attack Path Target Matrix ($\mathbf{Y} \in \{0, 1\}^{N \times N}$)
Ground-truth adjacency matrix where $\mathbf{Y}_{uv} = 1$ indicates edge $(u \to v)$ is traversed during the tactical lateral movement progression.

---

## 📈 Empirical Benchmarks & Model Comparison

Evaluated on held-out test partitions across **1,033 enterprise research graphs** with zero data leakage:

| Model Architecture | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Inference (ms) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dijkstra Shortest Path** | 0.412 | 0.534 | 0.465 | 0.612 | 0.384 | **0.4 ms** |
| **CVSS-Weighted Walk** | 0.521 | 0.610 | 0.562 | 0.698 | 0.481 | 0.6 ms |
| **Biased Random Walk** | 0.483 | 0.572 | 0.524 | 0.654 | 0.429 | 1.2 ms |
| **Node2Vec + Logistic Regression** | 0.645 | 0.689 | 0.666 | 0.764 | 0.592 | 8.4 ms |
| **Relational GCN (3 Layers)** | 0.782 | 0.814 | 0.798 | 0.884 | 0.741 | 1.1 ms |
| **Relational GraphSAGE (3 Layers)** | 0.812 | 0.835 | 0.823 | 0.902 | 0.776 | 1.3 ms |
| **AegisPath GAT (4-Head + Physics)** | **0.894** | **0.918** | **0.906** | **0.962** | **0.887** | **1.2 ms** |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Node.js 18+ and npm (optional for frontend development; pre-compiled standalone bundle is included)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/vaguemit/Aegis.git
cd Aegis

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Launch Backend & Dashboard
```bash
# Windows 1-Click Launch Script:
.\run_backend.ps1

# Or standard command:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to access the Command Center.

---

## 🧪 Testing & Verification

Run the full automated test suite (43 unit & integration tests covering data pipelines, models, losses, beam search, XAI attribution, VM simulation, and FastAPI endpoints):

```bash
pytest -v
```

### Run Model Training Pipeline
Train the GAT model across all 826 training graphs and save persistent checkpoints:
```bash
python scripts/train_full_models.py
```

### Run Experimentation Benchmarks
```bash
# Model comparison benchmark (Dijkstra vs GCN vs SAGE vs GAT)
python -m src.experiments.benchmark

# Feature ablation study (removing CVEs, SPNs, edge relations)
python -m src.experiments.ablation

# Scalability benchmark across varying node counts (20 to 1,000 nodes)
python -m src.experiments.scalability
```

---

## 📂 Repository Structure

```text
Aegis/
├── backend/
│   ├── main.py                  # FastAPI server & static bundle mounting
│   ├── graph_manager.py         # Graph cache & GNN checkpoint loader
│   ├── models.py                # Pydantic REST request/response schemas
│   └── routes/                  # API routes (graphs, predict, xai, defense, simulation, experiments)
├── configs/
│   └── config.yaml              # Centralized hyperparameters & paths
├── data/
│   └── _data_/                  # 1,033 preprocessed research AD graphs (.pt)
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main Command Center coordinator
│   │   ├── index.css            # Obsidian/Carbon dark theme design system
│   │   └── components/          # React components (NetworkGraphView, AttackPredictionPanel, etc.)
│   └── dist/                    # Pre-compiled high-performance production build
├── scripts/
│   └── train_full_models.py     # Offline full-dataset GNN training script
├── src/
│   ├── analysis/                # Advanced XAI, Integrated Gradients, MITRE & Counterfactuals
│   ├── data/                    # PIGNNDataset loader, Schema, and Synthetic Generator
│   ├── evaluation/              # Metrics, data leakage audit, and verification tools
│   ├── experiments/             # Trainer, baselines, ablation, and scalability runners
│   ├── graph/                   # Graph visualizers and layout tools
│   ├── models/                  # GAT, GCN, GraphSAGE, and Physics Losses
│   ├── search/                  # Constrained Beam Search & Security Feasibility
│   └── simulation/              # VM Engine, Hypervisors, Syslog, and Attack Player
├── tests/                       # 43 automated pytest test cases
├── pyproject.toml               # Build system configuration
└── requirements.txt             # Python package dependencies
```

---

## 🛡️ MITRE ATT&CK Attribution Matrix

| Technique ID | Technique Name | Tactic | Edge / Condition | Mitigation |
|:---|:---|:---|:---|:---|
| **T1190** | Exploit Public-Facing Application | Initial Access (`TA0001`) | `EdgeType.OPEN` on CVE Vulnerable Host | Apply security patch (KB5034441) |
| **T1078** | Valid Accounts / Admin Session | Defense Evasion (`TA0005`) | `EdgeType.HAS_SESSION` to Privileged User | Terminate stale admin sessions / Enforce MFA |
| **T1021.001** | Remote Desktop Protocol | Lateral Movement (`TA0008`) | `EdgeType.CAN_RDP` | Restrict RDP to jump boxes / Disable Port 3389 |
| **T1021.003** | Distributed Component Object Model | Lateral Movement (`TA0008`) | `EdgeType.EXECUTE_DCOM` | Block TCP Port 135 / Restrict RPC filters |
| **T1558.003** | Kerberoasting (SPN Request) | Credential Access (`TA0006`) | `has_spn = True` on User Account | Rotate to AES-256 / Enforce 25+ char passwords |
| **T1003.006** | DCSync (Directory Replication) | Credential Access (`TA0006`) | `EdgeType.DC_SYNC` / `GET_CHANGES_ALL` | Revoke replication rights from non-DC accounts |
| **T1069.002** | Domain Groups Discovery | Discovery (`TA0007`) | `EdgeType.MEMBER_OF` | Enforce Tiered Administrative Model |

---

## 📜 Citation & Academic References

1. **François Marin, Pierre-Emmanuel Arduin, and Myriam Merad**, *"Physics-Informed Graph Neural Networks for Attack Path Prediction"*, Journal of Cybersecurity and Privacy, 2025.
2. **Petar Veličković et al.**, *"Graph Attention Networks"*, International Conference on Learning Representations (ICLR), 2018.
3. **William L. Hamilton, Rex Ying, and Jure Leskovec**, *"Inductive Representation Learning on Large Graphs"*, Advances in Neural Information Processing Systems (NeurIPS), 2017.
4. **Mukund Sundararajan, Ankur Taly, and Qiqi Yan**, *"Axiomatic Attribution for Deep Networks"*, International Conference on Machine Learning (ICML), 2017.
5. **The MITRE Corporation**, *"MITRE ATT&CK® Enterprise Matrix v14"*, 2024.

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
