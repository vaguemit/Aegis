import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Layers, CheckCircle2, Award } from 'lucide-react';

export default function ExperimentsModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('benchmark');
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [ablationData, setAblationData] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    fetch('/api/experiments/benchmark')
      .then((res) => res.json())
      .then((data) => setBenchmarkData(data))
      .catch((err) => console.error('Error fetching benchmark:', err));

    fetch('/api/experiments/ablation')
      .then((res) => res.json())
      .then((data) => setAblationData(data))
      .catch((err) => console.error('Error fetching ablation:', err));
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(10px)',
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
          maxWidth: '900px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 25px 50px rgba(0,0,0,0.9)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
        }}
      >
        {/* Modal Header */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', background: 'rgba(6, 182, 212, 0.15)', borderRadius: '8px' }}>
              <BarChart3 size={20} color="#38BDF8" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#FFFFFF' }}>
                Academic Evaluation & Benchmark Suite
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Comparing GAT against Classical Baselines, Embedding Methods, and GNNs
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            Close
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{ padding: '12px 24px', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', gap: '8px' }}>
          <button
            className="btn-cyber"
            onClick={() => setActiveTab('benchmark')}
            style={{
              padding: '6px 14px',
              fontSize: '0.8rem',
              background: activeTab === 'benchmark' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
              border: activeTab === 'benchmark' ? '1px solid #38BDF8' : '1px solid transparent',
              color: activeTab === 'benchmark' ? '#FFFFFF' : 'var(--text-secondary)',
            }}
          >
            Experiment 1: Model Benchmark (7 Models)
          </button>

          <button
            className="btn-cyber"
            onClick={() => setActiveTab('ablation')}
            style={{
              padding: '6px 14px',
              fontSize: '0.8rem',
              background: activeTab === 'ablation' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
              border: activeTab === 'ablation' ? '1px solid #38BDF8' : '1px solid transparent',
              color: activeTab === 'ablation' ? '#FFFFFF' : 'var(--text-secondary)',
            }}
          >
            Experiment 2: Feature Ablation Study
          </button>
        </div>

        {/* Tab Content */}
        <div style={{ padding: '24px', overflowY: 'auto' }}>
          {activeTab === 'benchmark' && benchmarkData && (
            <div>
              <div style={{ padding: '12px 16px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.25)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Award size={20} color="#10B981" />
                <span style={{ fontSize: '0.82rem', color: '#D1FAE5' }}>
                  <strong>Key Finding:</strong> The Graph Attention Network (GAT) primary model achieves an F1-Score of <strong>0.9373</strong> and ROC-AUC of <strong>0.9620</strong>, outperforming classical shortest-path baselines by over <strong>+93% relative F1 gain</strong>.
                </span>
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Architecture</th>
                    <th style={{ padding: '10px' }}>Precision</th>
                    <th style={{ padding: '10px' }}>Recall</th>
                    <th style={{ padding: '10px' }}>F1-Score</th>
                    <th style={{ padding: '10px' }}>ROC-AUC</th>
                    <th style={{ padding: '10px' }}>PR-AUC</th>
                    <th style={{ padding: '10px' }}>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(benchmarkData).map(([model, metrics], idx) => {
                    const isGat = model.includes('GAT');
                    return (
                      <tr
                        key={idx}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          background: isGat ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                          fontWeight: isGat ? '700' : '400',
                        }}
                      >
                        <td style={{ padding: '10px', color: isGat ? '#38BDF8' : '#FFFFFF' }}>{model}</td>
                        <td style={{ padding: '10px' }}>{(metrics.precision * 100).toFixed(1)}%</td>
                        <td style={{ padding: '10px' }}>{(metrics.recall * 100).toFixed(1)}%</td>
                        <td style={{ padding: '10px', color: isGat ? '#34D399' : 'inherit' }}>{metrics.f1.toFixed(4)}</td>
                        <td style={{ padding: '10px' }}>{metrics.roc_auc.toFixed(4)}</td>
                        <td style={{ padding: '10px' }}>{metrics.pr_auc.toFixed(4)}</td>
                        <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{metrics.latency_ms.toFixed(1)}ms</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'ablation' && ablationData && (
            <div>
              <div style={{ padding: '12px 16px', background: 'rgba(56, 189, 248, 0.08)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.25)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <TrendingUp size={20} color="#38BDF8" />
                <span style={{ fontSize: '0.82rem', color: '#E0F2FE' }}>
                  <strong>Ablation Conclusion:</strong> Topology alone yields F1 = 0.6459. Incorporating vulnerability flags (+0.1914 F1) and Active Directory privileges (+0.0704 F1) is critical for predicting real-world lateral movement.
                </span>
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Feature Configuration</th>
                    <th style={{ padding: '10px' }}>Active Dimensions</th>
                    <th style={{ padding: '10px' }}>F1-Score</th>
                    <th style={{ padding: '10px' }}>ROC-AUC</th>
                    <th style={{ padding: '10px' }}>ΔF1 Gain</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(ablationData).map(([config, metrics], idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px', color: '#FFFFFF' }}>{config}</td>
                      <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{metrics.active_features}</td>
                      <td style={{ padding: '10px' }}>{metrics.f1.toFixed(4)}</td>
                      <td style={{ padding: '10px' }}>{metrics.roc_auc.toFixed(4)}</td>
                      <td style={{ padding: '10px', color: metrics.delta_f1_gain > 0 ? '#34D399' : 'var(--text-muted)' }}>
                        {metrics.delta_f1_gain >= 0 ? `+${metrics.delta_f1_gain.toFixed(4)}` : metrics.delta_f1_gain.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
