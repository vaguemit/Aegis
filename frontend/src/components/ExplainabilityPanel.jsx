import React from 'react';
import { Eye, Cpu, CheckCircle2, ChevronRight, Award, Zap, AlertTriangle } from 'lucide-react';

export default function ExplainabilityPanel({
  explainResult,
  onClose,
}) {
  if (!explainResult) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '750px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 20px 40px rgba(0,0,0,0.8)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
        }}
      >
        {/* Modal Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', background: 'rgba(6, 182, 212, 0.15)', borderRadius: '8px' }}>
              <Eye size={20} color="#38BDF8" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#FFFFFF' }}>
                GAT Attention & Explainability Attribution
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Multi-Head Relational Graph Attention Weight Analysis
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            Close
          </button>
        </div>

        {/* Modal Content Body */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Key Findings Bullet List */}
          <div style={{ padding: '14px', background: 'rgba(6, 182, 212, 0.08)', borderRadius: '10px', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: '#38BDF8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Award size={16} /> Explainable AI Strategic Findings
            </h4>
            <ul style={{ paddingLeft: '20px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {explainResult.key_findings.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>

          {/* Hop-by-Hop Attention & Feature Contribution */}
          <div>
            <h3 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Attention Weights & Feature Attribution by Hop
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {explainResult.edge_explanations.map((exp, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '0.88rem' }}>
                      <span style={{ color: '#38BDF8' }}>{exp.source_name}</span>
                      <ChevronRight size={14} color="var(--text-muted)" />
                      <span style={{ color: '#F43F5E' }}>{exp.target_name}</span>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                        Attention α: {(exp.gat_attention_score).toFixed(3)}
                      </span>
                      <span className="badge badge-rose" style={{ fontSize: '0.7rem' }}>
                        Likelihood: {(exp.predicted_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    {exp.summary}
                  </p>

                  {/* Feature Contribution Tags */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Top Drivers:</span>
                    {exp.top_contributing_features.map(([feat, score], fi) => (
                      <span key={fi} className="badge badge-cyan" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>
                        {feat} (+{score.toFixed(1)})
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
