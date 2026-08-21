import React from 'react';
import { Route, Target, Flame, ArrowRight, ShieldCheck, AlertOctagon, Eye, Crosshair } from 'lucide-react';
import LiveAttackTimeline from './LiveAttackTimeline';

export default function AttackPredictionPanel({
  graphData,
  selectedSourceIdx,
  onSelectSourceIdx,
  selectedTargetIdx,
  onSelectTargetIdx,
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
  const nodes = graphData?.nodes || [];

  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1F1F2A', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Flame size={16} color="#F43F5E" />
          <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF' }}>Attack Path Prediction</h3>
        </div>

        {predictionResult && (
          <button
            className="btn-cyber btn-outline"
            onClick={onOpenExplainability}
            style={{ fontSize: '0.72rem', padding: '3px 8px' }}
          >
            <Eye size={12} /> XAI Attribution
          </button>
        )}
      </div>

      {/* Origin & Destination Route Selector */}
      <div style={{ padding: '10px 12px', background: '#12121A', borderRadius: '8px', border: '1px solid #1E1E28', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div>
          <label style={{ fontSize: '0.72rem', color: '#38BDF8', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
            <Crosshair size={12} color="#38BDF8" /> Attacker Starting Foothold:
          </label>
          <select
            value={selectedSourceIdx}
            onChange={(e) => onSelectSourceIdx(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '6px 8px',
              background: '#09090D',
              color: '#FFFFFF',
              border: '1px solid #282836',
              borderRadius: '6px',
              fontSize: '0.76rem',
              outline: 'none',
            }}
          >
            {nodes.map((n) => (
              <option key={n.index} value={n.index}>
                {n.name} ({n.entity_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.72rem', color: '#F43F5E', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '3px' }}>
            <Target size={12} color="#F43F5E" /> Crown Jewel Target:
          </label>
          <select
            value={selectedTargetIdx}
            onChange={(e) => onSelectTargetIdx(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '6px 8px',
              background: '#09090D',
              color: '#FFFFFF',
              border: '1px solid #282836',
              borderRadius: '6px',
              fontSize: '0.76rem',
              outline: 'none',
            }}
          >
            {nodes.map((n) => (
              <option key={n.index} value={n.index}>
                {n.name} ({n.entity_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* If No Prediction Generated Yet */}
      {(!predictionResult || !predictionResult.paths || predictionResult.paths.length === 0) ? (
        <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Route size={32} color="var(--text-muted)" style={{ margin: '0 auto 8px auto' }} />
          <p style={{ fontSize: '0.76rem' }}>
            Select your starting foothold and target destination above, then click <strong>"Predict Paths"</strong> in the top navigation bar.
          </p>
        </div>
      ) : (
        <>
          {/* Critical Bottleneck Pivot Alert */}
          {predictionResult.bottleneck_node_name && (
            <div style={{ padding: '8px 10px', background: '#171012', borderRadius: '6px', border: '1px solid #33151B', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertOctagon size={18} color="#EF4444" style={{ flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '0.76rem', fontWeight: '700', color: '#FCA5A5' }}>
                  Chokepoint Pivot: {predictionResult.bottleneck_node_name}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  Critical asset where adversary flows converge. Interdicting this node stops lateral movement.
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
                  fontSize: '0.72rem',
                  background: activePathIndex === idx ? '#FFFFFF' : '#14141C',
                  border: activePathIndex === idx ? '1px solid #FFFFFF' : '1px solid #22222E',
                  color: activePathIndex === idx ? '#000000' : 'var(--text-secondary)',
                }}
              >
                Vector #{p.rank} ({(p.confidence_score * 100).toFixed(0)}%)
              </button>
            ))}
          </div>

          {/* Selected Path Statistics */}
          {predictionResult.paths[activePathIndex] && (
            <div style={{ padding: '8px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E2A', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', textAlign: 'center' }}>
              <div>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Confidence</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#F43F5E' }}>
                  {(predictionResult.paths[activePathIndex].confidence_score * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Hops</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#38BDF8' }}>
                  {predictionResult.paths[activePathIndex].hop_count} Hops
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Nodes</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#10B981' }}>
                  {predictionResult.paths[activePathIndex].nodes.length} Assets
                </div>
              </div>
            </div>
          )}

          {/* Live Attack Step Timeline Player */}
          <div>
            <h4 style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
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
          {predictionResult.paths[activePathIndex] && (
            <div>
              <h4 style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
                Lateral Movement Sequence
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {predictionResult.paths[activePathIndex].hops.map((hop, idx) => (
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
          )}
        </>
      )}
    </div>
  );
}
