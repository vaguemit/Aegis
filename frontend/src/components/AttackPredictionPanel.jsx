import React from 'react';
import { Route, Target, Flame, ArrowRight, ShieldCheck, AlertOctagon, Eye } from 'lucide-react';
import LiveAttackTimeline from './LiveAttackTimeline';

export default function AttackPredictionPanel({
  predictionResult,
  activePathIndex,
  onSelectPathIndex,
  onOpenExplainability,
  onOpenAdvancedXAI,
  timelineEvents,
  currentStepIndex,
  onStepChange,
  isPlaying,
  onTogglePlay,
  onReset,
}) {
  if (!predictionResult || !predictionResult.paths || predictionResult.paths.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', background: '#09090D', border: '1px solid #1E1E28' }}>
        <Route size={36} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
        <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Attack Path Simulator</h4>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '240px' }}>
          Click "Predict Paths" to trigger the Graph Attention Network (GAT) to forecast multi-hop lateral movement.
        </p>
      </div>
    );
  }

  const currentPath = predictionResult.paths[activePathIndex] || predictionResult.paths[0];

  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Execution Telemetry Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1F1F2A', paddingBottom: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Flame size={15} color="#F43F5E" />
            <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF' }}>Predicted Attack Vectors</h3>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Model: {predictionResult.model_used} • {predictionResult.execution_time_ms.toFixed(1)}ms
          </span>
        </div>

        <button
          className="btn-cyber btn-outline"
          onClick={onOpenExplainability}
          style={{ fontSize: '0.72rem', padding: '3px 8px' }}
        >
          <Eye size={12} /> XAI Attribution
        </button>
      </div>

      {/* Critical Bottleneck Pivot Alert */}
      {predictionResult.bottleneck_node_name && (
        <div style={{ padding: '8px 10px', background: '#171012', borderRadius: '6px', border: '1px solid #33151B', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertOctagon size={18} color="#EF4444" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#FCA5A5' }}>
              Bottleneck Asset: {predictionResult.bottleneck_node_name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Highest adversarial flow convergence. Interdicting this node severs lateral movement paths.
            </div>
          </div>
        </div>
      )}

      {/* Path Rank Switcher Tabs */}
      <div style={{ display: 'flex', gap: '4px' }}>
        {predictionResult.paths.map((p, idx) => (
          <button
            key={p.rank}
            onClick={() => onSelectPathIndex(idx)}
            className="btn-cyber"
            style={{
              flex: 1,
              padding: '5px 8px',
              fontSize: '0.74rem',
              background: activePathIndex === idx ? '#FFFFFF' : '#14141C',
              border: activePathIndex === idx ? '1px solid #FFFFFF' : '1px solid #22222E',
              color: activePathIndex === idx ? '#000000' : 'var(--text-secondary)',
            }}
          >
            Rank #{p.rank} ({(p.confidence_score * 100).toFixed(0)}%)
          </button>
        ))}
      </div>

      {/* Selected Path Statistics */}
      <div style={{ padding: '8px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E2A', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', textAlign: 'center' }}>
        <div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Confidence</span>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#F43F5E' }}>
            {(currentPath.confidence_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Lateral Hops</span>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#38BDF8' }}>
            {currentPath.hop_count} Hops
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Total Nodes</span>
          <div style={{ fontSize: '0.92rem', fontWeight: '800', color: '#10B981' }}>
            {currentPath.nodes.length}
          </div>
        </div>
      </div>

      {/* Live Attack Step Timeline Player */}
      <div>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Live Step-by-Step Playback
        </h4>
        <LiveAttackTimeline
          timelineEvents={timelineEvents}
          currentStepIndex={currentStepIndex}
          onStepChange={onStepChange}
          isPlaying={isPlaying}
          onTogglePlay={onTogglePlay}
          onReset={onReset}
        />
      </div>

      {/* Step-by-Step Lateral Movement Progression */}
      <div>
        <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Tactical Transition Sequence
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {currentPath.hops.map((hop, idx) => (
            <div
              key={idx}
              style={{
                padding: '7px 9px',
                background: '#12121A',
                borderRadius: '5px',
                border: '1px solid #1E1E28',
                fontSize: '0.74rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '600' }}>
                  <span style={{ color: '#38BDF8' }}>{hop.source_name}</span>
                  <ArrowRight size={10} color="var(--text-muted)" />
                  <span style={{ color: '#F43F5E' }}>{hop.target_name}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <button
                    className="btn-cyber btn-outline"
                    style={{ padding: '2px 5px', fontSize: '0.65rem' }}
                    onClick={() => onOpenAdvancedXAI(hop.source_idx, hop.target_idx)}
                    title="Decompose Multi-Head Attention"
                  >
                    XAI
                  </button>
                  <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>
                    {(hop.probability * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.68rem' }}>
                <span>Protocol: <code style={{ color: '#FBBF24' }}>{hop.edge_type}</code></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
