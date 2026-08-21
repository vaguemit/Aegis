import React from 'react';
import { Shield, Activity, Cpu, Play, PlusCircle, BarChart3, RefreshCw, Zap } from 'lucide-react';

export default function Navbar({
  selectedGraphId,
  graphs,
  onSelectGraph,
  onOpenGenerateModal,
  onOpenExperimentsModal,
  selectedModel,
  onSelectModel,
  isPredicting,
  onTriggerPredict,
  backendOnline,
}) {
  return (
    <header className="glass-panel" style={{ margin: '12px 16px', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #0284C7 0%, #06B6D4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)'
        }}>
          <Shield size={24} color="#FFFFFF" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em', background: 'linear-gradient(to right, #FFFFFF, #38BDF8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              AegisPath
            </h1>
            <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>GAT v2.0</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Enterprise Attack Path Prediction & Decision Support</p>
        </div>
      </div>

      {/* Network & Model Selector Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Graph Selection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>Topology:</label>
          <select
            value={selectedGraphId}
            onChange={(e) => onSelectGraph(e.target.value)}
            style={{
              background: 'rgba(17, 24, 39, 0.9)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '0.85rem',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>AI Model:</label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{
              background: 'rgba(17, 24, 39, 0.9)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '0.85rem',
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
          {isPredicting ? <RefreshCw className="animate-spin" size={16} /> : <Zap size={16} />}
          Predict Paths
        </button>
      </div>

      {/* Auxiliary Action Tools & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button className="btn-cyber btn-outline" onClick={onOpenGenerateModal}>
          <PlusCircle size={16} />
          Synthesize Network
        </button>

        <button className="btn-cyber btn-outline" onClick={onOpenExperimentsModal}>
          <BarChart3 size={16} />
          Benchmarks & Ablation
        </button>

        {/* Backend Heartbeat Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: backendOnline ? '#10B981' : '#EF4444',
            boxShadow: backendOnline ? '0 0 8px #10B981' : '0 0 8px #EF4444'
          }} />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {backendOnline ? 'AI Core Online' : 'Connecting...'}
          </span>
        </div>
      </div>
    </header>
  );
}
