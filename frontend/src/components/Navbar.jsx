import React, { useState } from 'react';
import {
  Shield,
  PlusCircle,
  BarChart3,
  RefreshCw,
  Zap,
  Server,
  Sparkles,
  Network,
  Cpu,
  Sliders,
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
  onQuickGenerateNodes,
  isGenerating,
}) {
  const [sliderNodes, setSliderNodes] = useState(60);

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
        gap: '10px',
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'nowrap' }}>
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
              fontSize: '0.74rem',
              fontWeight: '600',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '190px',
            }}
          >
            {DEMO_STORIES.map((s) => (
              <option key={s.id} value={s.id} style={{ background: '#12121A', color: '#FFFFFF' }}>
                {s.title}
              </option>
            ))}
          </select>
        </div>

        {/* Dynamic Node Count Slider */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#12121A',
            padding: '4px 10px',
            borderRadius: '6px',
            border: '1px solid #22222E',
          }}
          title="Adjust total network node scale (15 to 500 nodes)"
        >
          <Sliders size={12} color="#38BDF8" />
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>
            Nodes: <strong style={{ color: '#38BDF8' }}>{sliderNodes}</strong>
          </span>
          <input
            type="range"
            min="15"
            max="500"
            step="5"
            value={sliderNodes}
            onChange={(e) => setSliderNodes(Number(e.target.value))}
            style={{ width: '80px', accentColor: '#38BDF8', cursor: 'pointer' }}
          />
          <button
            className="btn-cyber"
            onClick={() => onQuickGenerateNodes && onQuickGenerateNodes(sliderNodes)}
            disabled={isGenerating}
            style={{
              padding: '3px 8px',
              fontSize: '0.68rem',
              background: '#38BDF8',
              color: '#000000',
              fontWeight: '800',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              opacity: isGenerating ? 0.7 : 1,
            }}
            title="Generate custom Active Directory network with this exact number of nodes"
          >
            {isGenerating ? <RefreshCw className="animate-spin" size={11} /> : null}
            {isGenerating ? 'Building...' : 'Apply'}
          </button>
        </div>

        {/* Topology Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', background: '#12121A', padding: '4px 8px', borderRadius: '6px', border: '1px solid #22222E' }}>
          <Network size={12} color="#A78BFA" />
          <select
            value={selectedGraphId}
            onChange={(e) => onSelectGraph(e.target.value)}
            style={{
              background: 'transparent',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.74rem',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '120px',
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
          <Cpu size={12} color="#10B981" />
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{
              background: 'transparent',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.74rem',
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

        {/* Predict Action Button */}
        <button
          className="btn-cyber btn-primary"
          onClick={onTriggerPredict}
          disabled={isPredicting}
          style={{
            padding: '5px 12px',
            fontSize: '0.75rem',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            flexShrink: 0,
            opacity: isPredicting ? 0.7 : 1,
          }}
        >
          {isPredicting ? <RefreshCw className="animate-spin" size={12} /> : <Zap size={12} />}
          Predict Paths
        </button>
      </div>

      {/* Right Tools & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
        <button
          className="btn-cyber btn-outline"
          onClick={onOpenVmModal}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
          title="Virtual Machine Hypervisors, Open Ports & Syslog Telemetry"
        >
          <Server size={12} /> VMs
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={onOpenExperimentsModal}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '4px' }}
          title="Run Model Comparisons, Ablation Studies & Scalability Benchmarks"
        >
          <BarChart3 size={12} /> Benchmarks
        </button>

        {/* Backend Heartbeat Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 7px',
            background: '#12121A',
            borderRadius: '6px',
            border: '1px solid #22222E',
            fontSize: '0.68rem',
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
