import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, ChevronRight, Terminal, ShieldAlert, Cpu, Activity } from 'lucide-react';

export default function LiveAttackTimeline({
  timelineEvents,
  currentStepIndex,
  onStepChange,
  isPlaying,
  onTogglePlay,
  onReset,
}) {
  if (!timelineEvents || timelineEvents.length === 0) {
    return (
      <div style={{ padding: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Run "Predict Paths" to generate synchronized real-time VM attack progression.
        </span>
      </div>
    );
  }

  const activeEvent = timelineEvents[currentStepIndex] || timelineEvents[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Player Controls Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#0F0F14', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className={`btn-cyber ${isPlaying ? 'btn-danger' : 'btn-primary'}`}
            onClick={onTogglePlay}
            style={{ padding: '5px 12px', fontSize: '0.78rem' }}
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            {isPlaying ? 'Pause' : 'Play Live'}
          </button>

          <button
            className="btn-cyber btn-outline"
            onClick={() => onStepChange(Math.min(timelineEvents.length - 1, currentStepIndex + 1))}
            disabled={currentStepIndex >= timelineEvents.length - 1}
            style={{ padding: '5px 10px', fontSize: '0.78rem' }}
          >
            <ChevronRight size={14} /> Step Next
          </button>

          <button
            className="btn-cyber btn-outline"
            onClick={onReset}
            style={{ padding: '5px 10px', fontSize: '0.78rem' }}
          >
            <RotateCcw size={13} />
          </button>
        </div>

        <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          Step {currentStepIndex + 1} / {timelineEvents.length}
        </span>
      </div>

      {/* Active Attack Transition Card */}
      <div style={{ padding: '12px', background: '#121218', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: '700' }}>
            <span style={{ color: '#38BDF8' }}>{activeEvent.source_vm}</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <span style={{ color: '#F43F5E' }}>{activeEvent.target_vm}</span>
          </div>

          <span className="badge badge-rose" style={{ fontSize: '0.68rem' }}>
            {(activeEvent.probability * 100).toFixed(1)}% Conf
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.74rem' }}>
          <div style={{ padding: '6px 8px', background: '#09090D', borderRadius: '4px', border: '1px solid #1F1F28' }}>
            <span style={{ color: 'var(--text-muted)' }}>Tactic: </span>
            <span style={{ color: '#E2E8F0', fontWeight: '600' }}>{activeEvent.mitre_tactic}</span>
          </div>
          <div style={{ padding: '6px 8px', background: '#09090D', borderRadius: '4px', border: '1px solid #1F1F28' }}>
            <span style={{ color: 'var(--text-muted)' }}>Technique: </span>
            <span style={{ color: '#FBBF24', fontWeight: '600' }}>{activeEvent.mitre_technique}</span>
          </div>
        </div>

        {/* Live Syslog Stream Terminal */}
        <div style={{ padding: '8px 10px', background: '#050508', borderRadius: '6px', border: '1px solid #181820', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#10B981', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
          <Terminal size={14} color="#10B981" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ wordBreak: 'break-all', lineHeight: '1.4' }}>
            {activeEvent.syslog}
          </div>
        </div>
      </div>
    </div>
  );
}
