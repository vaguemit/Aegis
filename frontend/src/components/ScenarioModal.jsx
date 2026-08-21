import React, { useState } from 'react';
import { PlusCircle, Sliders, RefreshCw } from 'lucide-react';

export default function ScenarioModal({ isOpen, onClose, onGenerate }) {
  const [scenarioName, setScenarioName] = useState('enterprise_custom');
  const [computers, setComputers] = useState(35);
  const [servers, setServers] = useState(8);
  const [users, setUsers] = useState(60);
  const [ous, setOus] = useState(4);
  const [cveProb, setCveProb] = useState(0.25);
  const [spnProb, setSpnProb] = useState(0.15);
  const [isGenerating, setIsGenerating] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    await onGenerate({
      scenario_name: scenarioName,
      num_computers: Number(computers),
      num_servers: Number(servers),
      num_users: Number(users),
      num_ous: Number(ous),
      cve_probability: Number(cveProb),
      spn_probability: Number(spnProb),
    });
    setIsGenerating(false);
    onClose();
  };

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
          maxWidth: '540px',
          padding: '24px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.8)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', background: 'rgba(6, 182, 212, 0.15)', borderRadius: '8px' }}>
              <Sliders size={20} color="#38BDF8" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#FFFFFF' }}>
                Synthesize Enterprise Network
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Parametric Active Directory Generator
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '4px 10px', fontSize: '0.8rem' }}>
            Cancel
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
              Scenario Identifier
            </label>
            <input
              type="text"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: '#FFFFFF',
                fontSize: '0.85rem',
              }}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Workstation Computers ({computers})
              </label>
              <input
                type="range"
                min="10"
                max="120"
                value={computers}
                onChange={(e) => setComputers(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Enterprise Servers ({servers})
              </label>
              <input
                type="range"
                min="2"
                max="30"
                value={servers}
                onChange={(e) => setServers(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Domain User Accounts ({users})
              </label>
              <input
                type="range"
                min="15"
                max="150"
                value={users}
                onChange={(e) => setUsers(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Organizational Units ({ous})
              </label>
              <input
                type="range"
                min="1"
                max="8"
                value={ous}
                onChange={(e) => setOus(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Vulnerability (CVE) Rate ({(cveProb * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0.05"
                max="0.80"
                step="0.05"
                value={cveProb}
                onChange={(e) => setCveProb(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Service SPN Rate ({(spnProb * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0.05"
                max="0.50"
                step="0.05"
                value={spnProb}
                onChange={(e) => setSpnProb(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="submit" className="btn-cyber btn-primary" disabled={isGenerating}>
              {isGenerating ? <RefreshCw className="animate-spin" size={16} /> : <PlusCircle size={16} />}
              Synthesize Topology
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
