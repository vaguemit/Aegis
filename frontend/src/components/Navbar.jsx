import React from 'react';
import {
  Shield,
  PlusCircle,
  BarChart3,
  RefreshCw,
  Zap,
  Server,
  Sparkles,
  Sliders,
  Network,
  Cpu,
} from 'lucide-react';
import { DEMO_STORIES } from './GuidedDemoBanner';

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
  currentStoryId,
  onSelectStory,
}) {
  return (
    <header
      style={{
        margin: '10px 14px 8px 14px',
        padding: '8px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#0B0B10',
        border: '1px solid #1E1E28',
        borderRadius: '10px',
        gap: '12px',
        flexWrap: 'nowrap',
      }}
    >
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '7px',
            background: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 12px rgba(255, 255, 255, 0.2)',
          }}
        >
          <Shield size={18} color="#000000" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '1.05rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#FFFFFF' }}>
              AegisPath
            </span>
            <span
              style={{
                fontSize: '0.62rem',
                padding: '1px 5px',
                background: '#1A1A24',
                border: '1px solid #282838',
                borderRadius: '4px',
                color: '#94A3B8',
                fontWeight: '600',
              }}
            >
              GNN SOC
            </span>
          </div>
        </div>
      </div>

      {/* Center Controls Group */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'nowrap' }}>
        {/* Story Scenario Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', background: '#12121A', padding: '4px 8px', borderRadius: '6px', border: '1px solid #22222E' }}>
          <Sparkles size={13} color="#38BDF8" />
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>Scenario:</span>
          <select
            value={currentStoryId}
            onChange={(e) => onSelectStory && onSelectStory(e.target.value)}
            style={{
              background: 'transparent',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.75rem',
              fontWeight: '600',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '210px',
            }}
          >
            {DEMO_STORIES.map((s) => (
              <option key={s.id} value={s.id} style={{ background: '#12121A', color: '#FFFFFF' }}>
                {s.title}
              </option>
            ))}
          </select>
        </div>

        {/* Network Topology Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', background: '#12121A', padding: '4px 8px', borderRadius: '6px', border: '1px solid #22222E' }}>
          <Network size={13} color="#A78BFA" />
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>Network:</span>
          <select
            value={selectedGraphId}
            onChange={(e) => onSelectGraph(e.target.value)}
            style={{
              background: 'transparent',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.75rem',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '140px',
            }}
          >
            {graphs.map((g) => (
              <option key={g.graph_id} value={g.graph_id} style={{ background: '#12121A', color: '#FFFFFF' }}>
                {g.graph_id} ({g.num_nodes}n)
              </option>
            ))}
          </select>
        </div>

        {/* AI Model Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', background: '#12121A', padding: '4px 8px', borderRadius: '6px', border: '1px solid #22222E' }}>
          <Cpu size={13} color="#10B981" />
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>AI:</span>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{
              background: 'transparent',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.75rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="gat" style={{ background: '#12121A' }}>GAT (Multi-Head)</option>
            <option value="graphsage" style={{ background: '#12121A' }}>GraphSAGE</option>
            <option value="gcn" style={{ background: '#12121A' }}>GCN</option>
            <option value="cvss" style={{ background: '#12121A' }}>CVSS-Walk</option>
            <option value="dijkstra" style={{ background: '#12121A' }}>Dijkstra</option>
          </select>
        </div>

        {/* Primary Prediction Action Button */}
        <button
          className="btn-cyber btn-primary"
          onClick={onTriggerPredict}
          disabled={isPredicting}
          style={{
            padding: '6px 14px',
            fontSize: '0.76rem',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            flexShrink: 0,
            opacity: isPredicting ? 0.7 : 1,
          }}
        >
          {isPredicting ? <RefreshCw className="animate-spin" size={13} /> : <Zap size={13} />}
          Predict Paths
        </button>
      </div>

      {/* Right Tools & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
        <button
          className="btn-cyber btn-outline"
          onClick={onOpenVmModal}
          style={{ padding: '5px 10px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          title="Virtual Machine Hypervisors, Open Ports & Syslog Telemetry"
        >
          <Server size={13} /> VMs
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={onOpenGenerateModal}
          style={{ padding: '5px 10px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          title="Synthesize Custom Network with Arbitrary Nodes and Edges"
        >
          <PlusCircle size={13} /> Custom Net
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={onOpenExperimentsModal}
          style={{ padding: '5px 10px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '5px' }}
          title="Run Model Comparisons, Ablation Studies & Scalability Benchmarks"
        >
          <BarChart3 size={13} /> Benchmarks
        </button>

        {/* Backend Heartbeat Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 8px',
            background: '#12121A',
            borderRadius: '6px',
            border: '1px solid #22222E',
            fontSize: '0.7rem',
          }}
        >
          <div
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: backendOnline ? '#10B981' : '#EF4444',
              boxShadow: backendOnline ? '0 0 6px #10B981' : '0 0 6px #EF4444',
            }}
          />
          <span style={{ color: 'var(--text-muted)' }}>{backendOnline ? 'Online' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
}
