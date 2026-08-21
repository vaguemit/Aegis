import React, { useState } from 'react';
import {
  Route,
  Target,
  Flame,
  ArrowRight,
  ShieldCheck,
  AlertOctagon,
  Eye,
  Crosshair,
  Layers,
  PlayCircle,
  Zap,
  RefreshCw,
} from 'lucide-react';
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
  isPredicting,
  onTriggerPredict,
}) {
  const [panelTab, setPanelTab] = useState('vectors'); // 'vectors' | 'timeline'
  const nodes = graphData?.nodes || [];

  return (
    <div
      style={{
        padding: '14px',
        height: '100%',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        background: '#0B0B10',
        border: '1px solid #1E1E28',
        borderRadius: '10px',
      }}
    >
      {/* Panel Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1A1A24', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Flame size={15} color="#F43F5E" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>Attack Vectors</h3>
        </div>

        {predictionResult && (
          <button
            className="btn-cyber btn-outline"
            onClick={onOpenExplainability}
            style={{ fontSize: '0.7rem', padding: '3px 7px' }}
          >
            <Eye size={11} /> XAI
          </button>
        )}
      </div>

      {/* Start and Target Pickers */}
      <div style={{ padding: '8px 10px', background: '#12121A', borderRadius: '8px', border: '1px solid #1E1E28', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div>
          <label style={{ fontSize: '0.7rem', color: '#38BDF8', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' }}>
            <Crosshair size={11} /> Start Foothold:
          </label>
          <select
            value={selectedSourceIdx}
            onChange={(e) => onSelectSourceIdx(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '4px 6px',
              background: '#09090D',
              color: '#FFFFFF',
              border: '1px solid #282836',
              borderRadius: '5px',
              fontSize: '0.74rem',
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
          <label style={{ fontSize: '0.7rem', color: '#F43F5E', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' }}>
            <Target size={11} /> Crown Jewel Target:
          </label>
          <select
            value={selectedTargetIdx}
            onChange={(e) => onSelectTargetIdx(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '4px 6px',
              background: '#09090D',
              color: '#FFFFFF',
              border: '1px solid #282836',
              borderRadius: '5px',
              fontSize: '0.74rem',
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

        {/* Quick Predict Action Inside Left Panel */}
        <button
          className="btn-cyber btn-primary"
          onClick={() => onTriggerPredict && onTriggerPredict(selectedSourceIdx, selectedTargetIdx)}
          disabled={isPredicting}
          style={{
            marginTop: '3px',
            width: '100%',
            padding: '5px 8px',
            fontSize: '0.74rem',
            fontWeight: '800',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px',
            background: '#F43F5E',
            border: 'none',
            color: '#FFFFFF',
          }}
        >
          {isPredicting ? <RefreshCw className="animate-spin" size={12} /> : <Zap size={12} />}
          {isPredicting ? 'Forecasting Paths...' : 'Predict Attack Trajectory'}
        </button>
      </div>

      {(!predictionResult || !predictionResult.paths || predictionResult.paths.length === 0) ? (
        <div style={{ padding: '24px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Route size={28} color="var(--text-muted)" style={{ margin: '0 auto 8px auto' }} />
          <p style={{ fontSize: '0.74rem', margin: 0, lineHeight: 1.4 }}>
            Click <strong>"Predict Attack Trajectory"</strong> above to forecast lateral movement paths from the selected foothold to target.
          </p>
        </div>
      ) : (
        <>
          {/* Segmented View Switcher: Vectors vs Timeline */}
          <div style={{ display: 'flex', background: '#12121A', padding: '2px', borderRadius: '6px', border: '1px solid #1E1E28' }}>
            <button
              onClick={() => setPanelTab('vectors')}
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: '0.72rem',
                fontWeight: '600',
                borderRadius: '4px',
                border: 'none',
                background: panelTab === 'vectors' ? '#FFFFFF' : 'transparent',
                color: panelTab === 'vectors' ? '#000000' : 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px',
              }}
            >
              <Layers size={11} /> Attack Vectors
            </button>
            <button
              onClick={() => setPanelTab('timeline')}
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: '0.72rem',
                fontWeight: '600',
                borderRadius: '4px',
                border: 'none',
                background: panelTab === 'timeline' ? '#FFFFFF' : 'transparent',
                color: panelTab === 'timeline' ? '#000000' : 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px',
              }}
            >
              <PlayCircle size={11} /> Live Player
            </button>
          </div>

          {panelTab === 'vectors' && (
            <>
              {/* Path Rank Switcher */}
              <div style={{ display: 'flex', gap: '4px' }}>
                {predictionResult.paths.map((p, idx) => (
                  <button
                    key={p.rank}
                    onClick={() => onSelectPathIndex(idx)}
                    className="btn-cyber"
                    style={{
                      flex: 1,
                      padding: '4px 6px',
                      fontSize: '0.7rem',
                      background: activePathIndex === idx ? '#FFFFFF' : '#14141C',
                      border: activePathIndex === idx ? '1px solid #FFFFFF' : '1px solid #22222E',
                      color: activePathIndex === idx ? '#000000' : 'var(--text-secondary)',
                    }}
                  >
                    Vector #{p.rank} ({(p.confidence_score * 100).toFixed(0)}%)
                  </button>
                ))}
              </div>

              {/* Path Metrics Bar */}
              {predictionResult.paths[activePathIndex] && (
                <div style={{ padding: '6px 8px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E2A', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px', textAlign: 'center' }}>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Confidence</span>
                    <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#F43F5E' }}>
                      {(predictionResult.paths[activePathIndex].confidence_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Hops</span>
                    <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#38BDF8' }}>
                      {predictionResult.paths[activePathIndex].hop_count} Hops
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Assets</span>
                    <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#10B981' }}>
                      {predictionResult.paths[activePathIndex].nodes.length}
                    </div>
                  </div>
                </div>
              )}

              {/* Hop List */}
              {predictionResult.paths[activePathIndex] && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  {predictionResult.paths[activePathIndex].hops.map((hop, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '6px 8px',
                        background: '#12121A',
                        borderRadius: '6px',
                        border: '1px solid #1E1E28',
                        fontSize: '0.72rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                          <span style={{ color: '#38BDF8' }}>{hop.source_name}</span>
                          <ArrowRight size={10} color="var(--text-muted)" />
                          <span style={{ color: '#F43F5E' }}>{hop.target_name}</span>
                        </div>
                        <button
                          className="btn-cyber btn-outline"
                          style={{ padding: '1px 4px', fontSize: '0.62rem' }}
                          onClick={() => onOpenAdvancedXAI(hop.source_idx, hop.target_idx)}
                        >
                          XAI
                        </button>
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                        Protocol: <code style={{ color: '#FBBF24' }}>{hop.edge_type}</code>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {panelTab === 'timeline' && (
            <div style={{ flex: 1 }}>
              <LiveAttackTimeline
                timelineEvents={timelineEvents}
                currentStepIndex={currentStepIndex}
                onStepChange={onStepChange}
                isPlaying={isPlaying}
                onTogglePlay={onTogglePlay}
                onReset={onReset}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
