import React from 'react';
import { Route, Target, Flame, ArrowRight, ShieldCheck, AlertOctagon, Clock, Percent } from 'lucide-react';

export default function AttackPredictionPanel({
  predictionResult,
  activePathIndex,
  onSelectPathIndex,
  onOpenExplainability,
}) {
  if (!predictionResult || !predictionResult.paths || predictionResult.paths.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <Route size={36} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
        <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Attack Path Simulator</h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '240px' }}>
          Click "Predict Paths" to trigger the Graph Attention Network (GAT) to compute adversarial trajectories.
        </p>
      </div>
    );
  }

  const currentPath = predictionResult.paths[activePathIndex] || predictionResult.paths[0];

  return (
    <div className="glass-panel" style={{ padding: '18px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Execution Telemetry Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Flame size={16} color="#F43F5E" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFFFFF' }}>Predicted Attack Paths</h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            Model: {predictionResult.model_used} • {predictionResult.execution_time_ms.toFixed(1)}ms
          </span>
        </div>

        <button
          className="btn-cyber btn-outline"
          onClick={onOpenExplainability}
          style={{ fontSize: '0.75rem', padding: '4px 8px' }}
        >
          View XAI Attribution
        </button>
      </div>

      {/* Critical Bottleneck Pivot Alert */}
      {predictionResult.bottleneck_node_name && (
        <div style={{ padding: '10px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.25)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertOctagon size={20} color="#EF4444" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#FCA5A5' }}>
              Critical Pivot Bottleneck: {predictionResult.bottleneck_node_name}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Highest adversarial flow convergence. Interdicting this node severs all predicted attack vectors.
            </div>
          </div>
        </div>
      )}

      {/* Path Rank Switcher Tabs */}
      <div style={{ display: 'flex', gap: '6px' }}>
        {predictionResult.paths.map((p, idx) => (
          <button
            key={p.rank}
            onClick={() => onSelectPathIndex(idx)}
            className="btn-cyber"
            style={{
              flex: 1,
              padding: '6px 10px',
              fontSize: '0.78rem',
              background: activePathIndex === idx ? 'rgba(244, 63, 94, 0.2)' : 'rgba(255, 255, 255, 0.04)',
              border: activePathIndex === idx ? '1px solid rgba(244, 63, 94, 0.5)' : '1px solid var(--border-subtle)',
              color: activePathIndex === idx ? '#FB7185' : 'var(--text-secondary)',
            }}
          >
            Rank #{p.rank} ({(p.confidence_score * 100).toFixed(0)}%)
          </button>
        ))}
      </div>

      {/* Selected Path Statistics */}
      <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', textAlign: 'center' }}>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Confidence</span>
          <div style={{ fontSize: '1rem', fontWeight: '800', color: '#F43F5E' }}>
            {(currentPath.confidence_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Lateral Hops</span>
          <div style={{ fontSize: '1rem', fontWeight: '800', color: '#38BDF8' }}>
            {currentPath.hop_count} Hops
          </div>
        </div>
        <div>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Nodes</span>
          <div style={{ fontSize: '1rem', fontWeight: '800', color: '#10B981' }}>
            {currentPath.nodes.length}
          </div>
        </div>
      </div>

      {/* Step-by-Step Lateral Movement Progression */}
      <div>
        <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '8px' }}>
          Tactical Movement Chain
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {currentPath.hops.map((hop, idx) => (
            <div
              key={idx}
              style={{
                padding: '8px 10px',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.78rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600' }}>
                  <span style={{ color: '#38BDF8' }}>{hop.source_name}</span>
                  <ArrowRight size={12} color="var(--text-muted)" />
                  <span style={{ color: '#F43F5E' }}>{hop.target_name}</span>
                </div>
                <span className="badge badge-rose" style={{ fontSize: '0.68rem' }}>
                  {(hop.probability * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.72rem' }}>
                <span>Protocol: <code style={{ color: '#FBBF24' }}>{hop.edge_type}</code></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
