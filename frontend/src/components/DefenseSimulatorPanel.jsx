import React from 'react';
import { ShieldCheck, TrendingDown, Sparkles, CheckCircle2 } from 'lucide-react';

export default function DefenseSimulatorPanel({
  defenseResult,
  recommendations,
  onApplyRecommendation,
}) {
  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1F1F2A', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={16} color="#10B981" />
          <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF' }}>Counterfactual Defense</h3>
        </div>
        <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>AI Decision Support</span>
      </div>

      {/* Active Counterfactual Simulation Outcome */}
      {defenseResult ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Delta Risk Meter */}
          <div style={{ padding: '10px 12px', background: '#0E1713', borderRadius: '8px', border: '1px solid #18382B' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.74rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Risk Reduction (ΔRisk)</span>
              <span className="badge badge-emerald" style={{ fontSize: '0.74rem' }}>
                <TrendingDown size={13} /> -{defenseResult.risk_reduction_pct.toFixed(1)}%
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', textAlign: 'center' }}>
              <div style={{ padding: '5px', background: '#09090D', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Before Action</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#F43F5E' }}>
                  {(defenseResult.original_risk_score * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ padding: '5px', background: '#09090D', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>After Mitigation</span>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#10B981' }}>
                  {(defenseResult.mitigated_risk_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <p style={{ fontSize: '0.72rem', color: '#D1FAE5', marginTop: '8px', lineHeight: '1.4' }}>
              {defenseResult.recommendation_verdict}
            </p>
          </div>
        </div>
      ) : (
        <div style={{ padding: '10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.74rem' }}>
          Select a node or click an optimal mitigation below to simulate counterfactual risk reduction.
        </div>
      )}

      {/* Automated Mitigation Recommendations */}
      <div>
        <h4 style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
          <Sparkles size={13} color="#FBBF24" /> Optimal Defenses
        </h4>

        {recommendations && recommendations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 10px',
                  background: '#12121A',
                  borderRadius: '6px',
                  border: '1px solid #1E1E28',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#FFFFFF' }}>
                    {rec.action_type}
                  </span>
                  <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>
                    -{rec.risk_reduction_pct.toFixed(0)}% Risk
                  </span>
                </div>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  {rec.action_description}
                </p>
                <button
                  className="btn-cyber btn-success"
                  onClick={() => onApplyRecommendation(rec)}
                  style={{ width: '100%', fontSize: '0.72rem', padding: '4px 8px' }}
                >
                  <CheckCircle2 size={11} />
                  Simulate This Defense
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', padding: '8px' }}>
            Run "Predict Paths" to generate automated defense recommendations.
          </div>
        )}
      </div>
    </div>
  );
}
