import React from 'react';
import { Eye, Layers, ShieldCheck, Activity, Cpu, X, Compass } from 'lucide-react';

export default function MultiHeadXAIModal({ isOpen, onClose, xaiData }) {
  if (!isOpen || !xaiData) return null;

  const heads = xaiData.head_attentions || [];
  const igScores = xaiData.integrated_gradients_saliency || {};
  const mitre = xaiData.mitre_ttp || {};

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(12px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#09090D',
          border: '1px solid #2B2B38',
          boxShadow: '0 25px 60px rgba(0,0,0,0.95)',
        }}
      >
        {/* Header */}
        <div style={{ padding: '16px 22px', borderBottom: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', background: '#181822', borderRadius: '8px', border: '1px solid #333345' }}>
              <Eye size={20} color="#FFFFFF" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#FFFFFF' }}>
                Multi-Head GAT Attention Decomposition & MITRE ATT&CK Attribution
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Edge Transition: {xaiData.source_name} → {xaiData.target_name} ({xaiData.predicted_probability * 100}% Confidence)
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 10px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '22px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Tactical Rationale Banner */}
          <div style={{ padding: '12px 16px', background: '#12121A', borderRadius: '8px', border: '1px solid #282836', fontSize: '0.8rem', color: '#E2E8F0', lineHeight: '1.4' }}>
            <span style={{ fontWeight: '700', color: '#38BDF8' }}>Tactical Assessment: </span>
            {xaiData.tactical_rationale}
          </div>

          {/* Section 1: Multi-Head Attention Heads 1..4 */}
          <div>
            <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Multi-Head Attention Distribution (4 Relational Heads)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {heads.map((h, i) => (
                <div key={i} style={{ padding: '12px', background: '#101016', borderRadius: '8px', border: '1px solid #22222E' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: '700', color: '#FFFFFF' }}>{h.semantic_role}</span>
                    <span className="badge badge-obsidian" style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                      α = {h.attention_weight.toFixed(3)}
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '4px', background: '#1F1F2A', borderRadius: '2px', overflow: 'hidden', marginBottom: '6px' }}>
                    <div style={{ width: `${Math.min(100, h.attention_weight * 100)}%`, height: '100%', background: '#FFFFFF' }} />
                  </div>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{h.interpretation}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Integrated Gradients Feature Saliency */}
          <div>
            <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Integrated Gradients Feature Saliency Attribution
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {Object.entries(igScores).slice(0, 6).map(([feat, score], i) => (
                <div key={i} style={{ padding: '8px 12px', background: '#101016', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.78rem', color: '#FFFFFF', fontWeight: '500' }}>{feat}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '120px', height: '4px', background: '#1F1F2A', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, score * 200)}%`, height: '100%', background: '#10B981' }} />
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', width: '45px', textAlign: 'right' }}>
                      +{(score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: MITRE ATT&CK Matrix Alignment */}
          {mitre.technique_id && (
            <div style={{ padding: '14px', background: '#121218', borderRadius: '8px', border: '1px solid #282836' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Compass size={16} color="#FBBF24" />
                <span style={{ fontSize: '0.84rem', fontWeight: '700', color: '#FFFFFF' }}>
                  MITRE ATT&CK: {mitre.technique_id} ({mitre.technique_name})
                </span>
                <span className="badge badge-amber" style={{ fontSize: '0.68rem' }}>{mitre.tactic}</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                {mitre.description}
              </p>
              <div style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
                <strong>Mitigations: </strong>{mitre.mitigations?.join(', ')}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
