# AegisPath: AI-Powered Enterprise Attack Path Prediction and Decision Support System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AegisPath** is a research-grade, explainable graph learning framework designed for proactive cybersecurity risk assessment and attack path prediction in enterprise and Active Directory (AD) networks.

Unlike traditional vulnerability scanners that assess assets in isolation or static attack graphs that compute reachability without tactical likelihood, AegisPath leverages **Graph Attention Networks (GAT)** to learn high-risk lateral movement patterns, predict the most probable multi-hop attack trajectories, provide attention-based explainability, and simulate **counterfactual defensive mitigations** in real time.

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │            Enterprise Network Graph          │
                    │   (Nodes: Users, Computers, Domains, GPOs)   │
                    │   (Edges: AdminTo, CanRDP, DCSync, etc.)     │
                    └───────────────────────┬──────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────┐
                    │      Heterogeneous Feature Engineering       │
                    │  - 20-dim Entity, OS & Security Properties   │
                    │  - 16-channel Relational Adjacency Tensor    │
                    └───────────────────────┬──────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────┐
                    │          Primary Model: Multi-Head GAT       │
                    │  - Relational Attention Weighting            │
                    │  - Edge-Pair Likelihood Predictor P(u -> v)  │
                    └───────────────────────┬──────────────────────┘
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────┐
                    │        Constrained Beam Search Engine        │
                    │  - Security Precondition Feasibility Filter  │
                    │  - Top-K Multi-Hop Attack Path Reconstruction│
                    └───────────────────────┬──────────────────────┘
                                            │
                    ┌───────────────────────┼──────────────────────┐
                    ▼                       ▼                      ▼
           [ Explainability ]      [ Counterfactual ]     [ Research Benchmark ]
         - GAT Attention Scores   - Patch Simulation      - GAT vs GCN/SAGE
         - Pivot Vulnerability    - Delta Risk Analysis   - Feature Ablation
         - Attribution Heatmaps   - Path Diversion        - Scalability 20-1000
```

---

## 🔬 Core Features & Research Contributions

1. **100% From-Scratch Graph Learning Pipeline**:
   - Primary **Graph Attention Network (GAT)** with multi-head relational attention.
   - Comprehensive baseline zoo: **Dijkstra Shortest Path**, **CVSS-Weighted Walk**, **Biased Random Walk**, **Node2Vec + Link Classifier**, **Graph Convolutional Networks (GCN)**, and **GraphSAGE**.
2. **Security Feasibility-Constrained Path Search**:
   - Decoupled edge-level attack probability estimation and Top-$K$ beam search that guarantees zero invalid hops or unexploitable permissions.
3. **Counterfactual Defense Engine**:
   - Dynamically simulates mitigations (patching CVEs, disabling legacy protocols like SMB/RDP, revoking excessive privileges) on a cloned graph state to compute real-time $\Delta \text{Risk}$ and attack path rerouting.
4. **Attention-Based Explainability**:
   - Extracts attention weights $\alpha_{ij}$ from GAT layers to show administrators *why* an edge was flagged as high-risk.
5. **Full-Stack Security Operations Dashboard**:
   - High-throughput **FastAPI** backend + modern **React / TypeScript / Cytoscape.js** interactive canvas.

---

## 📊 Dataset & Mathematical Formulation

Each network environment $\mathcal{G}_i$ is represented as a triple:

$$\mathcal{G}_i = (\mathbf{X}_i, \mathbf{A}_i, \mathbf{Y}_i)$$

* **Adjacency Tensor $\mathbf{A}_i \in \mathbb{R}^{|V| \times |V| \times 16}$**: 16 directed Active Directory relationship types (`AdminTo`, `AllowedToDelegate`, `CanRDP`, `Contains`, `DCSync`, `ExecuteDCOM`, `GenericAll`, `GetChanges`, `GetChangesAll`, `GpLink`, `HasSession`, `MemberOf`, `Open`, `Owns`, `WriteDacl`, `WriteOwner`).
* **Feature Matrix $\mathbf{X}_i \in \mathbb{R}^{|V| \times 20}$**: 20 one-hot and boolean node features (Entity Types, OS versions, `enabled`, `hasspn`, `highvalue`, `is_vulnerable`, `target`, `owned`).
* **Target Matrix $\mathbf{Y}_i \in \{0, 1\}^{|V| \times |V|}$**: Ground-truth binary attack path indicator matrix where $\mathbf{Y}_{uv} = 1$ denotes edge $(u \to v)$ is on the critical attack path.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/vaguemit/Aegis.git
cd Aegis

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
pytest tests/ -v
```

### 3. Run Experiments & Baselines

```bash
# Run model comparison benchmark (Dijkstra vs CVSS-Walk vs GCN vs GraphSAGE vs GAT)
python -m src.experiments.benchmark

# Run feature ablation study
python -m src.experiments.ablation

# Run scalability benchmark (20 to 1000 nodes)
python -m src.experiments.scalability
```

### 4. Launch Backend & Dashboard

```bash
# Start FastAPI backend
uvicorn backend.main:app --reload --port 8000
```

---

## 📚 Citation & References

* François Marin, Pierre-Emmanuel Arduin, and Myriam Merad, *"Physics-Informed Graph Neural Networks for Attack Path Prediction"*, Journal of Cybersecurity and Privacy, 2025.
* Veličković, P., et al., *"Graph Attention Networks"*, ICLR 2018.
* Hamilton, W., et al., *"Inductive Representation Learning on Large Graphs"*, NeurIPS 2017.
