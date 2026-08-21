import React from 'react';
import { ShieldCheck, TrendingDown, Scissors, ArrowDownRight, Sparkles, CheckCircle2, Wrench } from 'lucide-react';

export default function DefenseSimulatorPanel({
  defenseResult,
  recommendations,
  onApplyRecommendation,
}) {
  return (
    <div className="glass-panel" style={{ padding: '18px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={18} color="#10B981" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFFFFF' }}>Counterfactual Defense</h3>
        </div>
        <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>AI Decision Support</span>
      </div>

      {/* Active Counterfactual Simulation Outcome */}
      {defenseResult ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Delta Risk Meter */}
          <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Risk Reduction (ΔRisk)</span>
              <span className="badge badge-emerald" style={{ fontSize: '0.78rem' }}>
                <TrendingDown size={14} /> -{defenseResult.risk_reduction_pct.toFixed(1)}%
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', textAlign: 'center' }}>
              <div style={{ padding: '6px', background: 'rgba(0,0,0,0.3)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Before Action</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#F43F5E' }}>
                  {(defenseResult.original_risk_score * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ padding: '6px', background: 'rgba(0,0,0,0.3)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>After Mitigation</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#10B981' }}>
                  {(defenseResult.mitigated_risk_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <p style={{ fontSize: '0.74rem', color: '#D1FAE5', marginTop: '10px', lineHeight: '1.4' }}>
              {defenseResult.recommendation_verdict}
            </p>
          </div>
        </div>
      ) : (
        <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
          Select a node or click an optimal mitigation below to simulate counterfactual risk reduction.
        </div>
      )}

      {/* Automated Mitigation Recommendations */}
      <div>
        <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} color="#FBBF24" /> Top Recommended Defenses
        </h4>

        {recommendations && recommendations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 12px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: '700', color: '#FFFFFF' }}>
                    {rec.action_type}
                  </span>
                  <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>
                    -{rec.risk_reduction_pct.toFixed(0)}% Risk
                  </span>
                </div>
                <p style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  {rec.action_description}
                </p>
                <button
                  className="btn-cyber btn-success"
                  onClick={() => onApplyRecommendation(rec)}
                  style={{ width: '100%', fontSize: '0.75rem', padding: '5px 10px' }}
                >
                  <CheckCircle2 size={12} />
                  Simulate This Defense
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', padding: '10px' }}>
            Run "Predict Paths" to generate automated defense recommendations.
          </div>
        )}
      </div>
    </div>
  );
}
