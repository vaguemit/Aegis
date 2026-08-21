import React from 'react';
import { Shield, Activity, Cpu, PlusCircle, BarChart3, RefreshCw, Zap, Server } from 'lucide-react';

export default function Navbar({
  selectedGraphId,
  graphs,
  onSelectGraph,
  onOpenGenerateModal,
  onOpenExperimentsModal,
  onOpenVmModal,
  selectedModel,
  onSelectModel,
  isPredicting,
  onTriggerPredict,
  backendOnline,
}) {
  return (
    <header className="glass-panel" style={{ margin: '10px 14px', padding: '10px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(255, 255, 255, 0.2)'
        }}>
          <Shield size={20} color="#000000" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.15rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#FFFFFF' }}>
              AegisPath
            </h1>
            <span className="badge badge-obsidian" style={{ fontSize: '0.65rem' }}>GAT v2.0</span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Enterprise Attack Path Prediction & Decision Support</p>
        </div>
      </div>

      {/* Network & Model Selector Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Graph Selection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: '600' }}>Topology:</label>
          <select
            value={selectedGraphId}
            onChange={(e) => onSelectGraph(e.target.value)}
            style={{
              background: '#12121A',
              color: 'var(--text-primary)',
              border: '1px solid #282836',
              borderRadius: '6px',
              padding: '5px 10px',
              fontSize: '0.8rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            {graphs.map((g) => (
              <option key={g.graph_id} value={g.graph_id}>
                {g.graph_id} ({g.num_nodes} nodes, {g.num_edges} edges)
              </option>
            ))}
          </select>
        </div>

        {/* GNN Model Selection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: '600' }}>AI Model:</label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{
              background: '#12121A',
              color: 'var(--text-primary)',
              border: '1px solid #282836',
              borderRadius: '6px',
              padding: '5px 10px',
              fontSize: '0.8rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="gat">GAT (Primary - Multi-Head Attention)</option>
            <option value="graphsage">GraphSAGE (Inductive Neighborhood)</option>
            <option value="gcn">GCN (Relational Laplacian)</option>
            <option value="cvss">CVSS-Weighted Walk (Baseline)</option>
            <option value="dijkstra">Dijkstra Shortest Path (Baseline)</option>
          </select>
        </div>

        {/* Predict Trigger Button */}
        <button
          className="btn-cyber btn-primary"
          onClick={onTriggerPredict}
          disabled={isPredicting}
          style={{ opacity: isPredicting ? 0.7 : 1 }}
        >
          {isPredicting ? <RefreshCw className="animate-spin" size={14} /> : <Zap size={14} />}
          Predict Paths
        </button>
      </div>

      {/* Auxiliary Action Tools & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button className="btn-cyber btn-outline" onClick={onOpenVmModal}>
          <Server size={14} />
          VM Infrastructure
        </button>

        <button className="btn-cyber btn-outline" onClick={onOpenGenerateModal}>
          <PlusCircle size={14} />
          Synthesize Network
        </button>

        <button className="btn-cyber btn-outline" onClick={onOpenExperimentsModal}>
          <BarChart3 size={14} />
          Benchmarks & Ablation
        </button>

        {/* Backend Heartbeat Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 8px', background: '#12121A', borderRadius: '6px', border: '1px solid #22222E' }}>
          <div style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            backgroundColor: backendOnline ? '#10B981' : '#EF4444',
            boxShadow: backendOnline ? '0 0 6px #10B981' : '0 0 6px #EF4444'
          }} />
          <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            {backendOnline ? 'AI Core Online' : 'Connecting...'}
          </span>
        </div>
      </div>
    </header>
  );
}
