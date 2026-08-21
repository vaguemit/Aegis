import React, { useState } from 'react';
import {
  ShieldCheck,
  TrendingDown,
  Sparkles,
  CheckCircle2,
  Terminal,
  Server,
  AlertTriangle,
  RotateCcw,
  FileCode,
} from 'lucide-react';

export default function DefenseSimulatorPanel({
  defenseResult,
  recommendations,
  onApplyRecommendation,
}) {
  const [showLogs, setShowLogs] = useState(true);

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
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1A1A24', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={16} color="#10B981" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>Counterfactual Defense</h3>
        </div>
        <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>AI Decision Engine</span>
      </div>

      {/* Active Defense Mitigation Card */}
      {defenseResult ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Delta Risk Meter */}
          <div style={{ padding: '10px 12px', background: '#0B1510', borderRadius: '8px', border: '1px solid #163B2C' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: '700', color: '#34D399' }}>
                🛡️ Security Hotfix Applied
              </span>
              <span className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
                <TrendingDown size={12} /> -{defenseResult.risk_reduction_pct.toFixed(1)}% Risk
              </span>
            </div>

            {/* Risk Reduction Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', textAlign: 'center', marginBottom: '8px' }}>
              <div style={{ padding: '5px', background: '#09090D', borderRadius: '5px', border: '1px solid #1E1E28' }}>
                <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Before Action</span>
                <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#F43F5E' }}>
                  {(defenseResult.original_risk_score * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ padding: '5px', background: '#09090D', borderRadius: '5px', border: '1px solid #1E1E28' }}>
                <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>After Mitigation</span>
                <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#10B981' }}>
                  {(defenseResult.mitigated_risk_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Realistic CVE Bulletin Specifications */}
            <div style={{ padding: '8px 10px', background: '#0E0E16', borderRadius: '6px', border: '1px solid #1E1E28', fontSize: '0.7rem', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Security Bulletin:</span>
                <strong style={{ color: '#38BDF8' }}>{defenseResult.kb_article || 'KB5034441'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Remediated Flaw:</span>
                <strong style={{ color: '#FBBF24' }}>{defenseResult.cve_id || 'CVE-2020-1472'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Patched Driver/Service:</span>
                <code style={{ color: '#A78BFA', fontSize: '0.66rem' }}>{defenseResult.patched_service || 'lanmanserver / srv2.sys'}</code>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>CVSS Rating:</span>
                <span>
                  <s style={{ color: '#EF4444' }}>{defenseResult.cvss_before || 9.8} (Critical)</s> ➔ <strong style={{ color: '#10B981' }}>0.0 (Mitigated)</strong>
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.7rem', color: '#D1FAE5', marginTop: '6px', marginBottom: '4px', lineHeight: '1.3' }}>
              {defenseResult.recommendation_verdict}
            </p>
          </div>

          {/* Live WSUS / Deployment Terminal Logs */}
          <div style={{ padding: '8px 10px', background: '#07070A', borderRadius: '6px', border: '1px solid #1A1A24' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                marginBottom: showLogs ? '6px' : '0',
              }}
              onClick={() => setShowLogs(!showLogs)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.7rem', fontWeight: '700', color: '#94A3B8' }}>
                <Terminal size={12} color="#38BDF8" />
                <span>WSUS / Hypervisor Deployment Audit</span>
              </div>
              <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>{showLogs ? 'Hide ▲' : 'Show ▼'}</span>
            </div>

            {showLogs && (
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '2px', maxHeight: '110px', overflowY: 'auto', background: '#050508', padding: '6px', borderRadius: '4px', border: '1px solid #14141E' }}>
                {defenseResult.deployment_logs && defenseResult.deployment_logs.length > 0 ? (
                  defenseResult.deployment_logs.map((log, lIdx) => (
                    <div key={lIdx} style={{ color: log.includes('SEVERED') || log.includes('successfully') ? '#10B981' : log.includes('Hotpatch') ? '#38BDF8' : '#94A3B8' }}>
                      {log}
                    </div>
                  ))
                ) : (
                  <>
                    <div style={{ color: '#38BDF8' }}>[00:00.12] [WSUS] Pushing KB5034441 cumulative hotfix package...</div>
                    <div style={{ color: '#94A3B8' }}>[00:00.45] [Hypervisor] Creating pre-patch VM snapshot: snap_pre_patch_01... OK</div>
                    <div style={{ color: '#94A3B8' }}>[00:01.02] [DISM] Installing Windows10.0-KB5034441-x64.cab...</div>
                    <div style={{ color: '#10B981' }}>[00:01.48] [Kernel] Remediating buffer overflow in srv2.sys... OK</div>
                    <div style={{ color: '#10B981' }}>[00:02.10] [GNN Engine] Attack reachability re-evaluated: Path SEVERED (-100%).</div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ padding: '16px 12px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
          Click <strong>"Simulate Patching Vulnerability"</strong> on any node or select a recommended mitigation below to test counterfactual risk reduction.
        </div>
      )}

      {/* Automated Mitigation Recommendations */}
      <div>
        <h4 style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '5px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Sparkles size={11} color="#FBBF24" /> Top Recommended Fixes
        </h4>

        {recommendations && recommendations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                style={{
                  padding: '7px 9px',
                  background: '#12121A',
                  borderRadius: '6px',
                  border: '1px solid #1E1E28',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ fontSize: '0.74rem', fontWeight: '700', color: '#FFFFFF' }}>
                    {rec.action_type}
                  </span>
                  <span className="badge badge-emerald" style={{ fontSize: '0.62rem' }}>
                    -{rec.risk_reduction_pct.toFixed(0)}% Risk
                  </span>
                </div>
                <p style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '5px', lineHeight: 1.2 }}>
                  {rec.action_description}
                </p>
                <button
                  className="btn-cyber btn-success"
                  onClick={() => onApplyRecommendation(rec)}
                  style={{ width: '100%', fontSize: '0.68rem', padding: '3px 6px' }}
                >
                  <CheckCircle2 size={10} />
                  Simulate This Defense
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center', padding: '8px' }}>
            Run "Predict Paths" to generate automated defense recommendations.
          </div>
        )}
      </div>
    </div>
  );
}
