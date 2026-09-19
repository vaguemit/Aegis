import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, Layers, Network, ShieldAlert, Cpu, Sparkles, X, Database, Upload, FileText, CheckCircle2 } from 'lucide-react';

export default function ScenarioModal({ isOpen, onClose, onGenerate, onGraphLoaded }) {
  const [activeTab, setActiveTab] = useState('BLOODHOUND'); // 'BLOODHOUND' | 'SYNTHETIC'

  // BloodHound Tab State
  const [bhLoading, setBhLoading] = useState(false);
  const [bhFeedback, setBhFeedback] = useState(null);
  const [customJson, setCustomJson] = useState('');

  // Synthetic Tab State
  const [scenarioName, setScenarioName] = useState('enterprise_scenario');
  const [useTargetNodes, setUseTargetNodes] = useState(true);
  const [targetNodes, setTargetNodes] = useState(60);
  const [edgeMultiplier, setEdgeMultiplier] = useState(3.5);
  const [cveProb, setCveProb] = useState(0.25);
  const [spnProb, setSpnProb] = useState(0.15);

  // Detailed granular controls
  const [computers, setComputers] = useState(30);
  const [servers, setServers] = useState(8);
  const [users, setUsers] = useState(40);
  const [ous, setOus] = useState(4);
  const [dcs, setDcs] = useState(2);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (useTargetNodes) {
      const overhead = 1 + dcs + ous + 3 + 5;
      const remaining = Math.max(5, targetNodes - overhead);
      const srv = Math.max(2, Math.round(remaining * 0.20));
      const ws = Math.max(2, Math.round(remaining * 0.45));
      const usr = Math.max(1, remaining - (srv + ws));
      setServers(srv);
      setComputers(ws);
      setUsers(usr);
    }
  }, [targetNodes, useTargetNodes]);

  if (!isOpen) return null;

  const calculatedNodes = useTargetNodes ? targetNodes : (1 + dcs + ous + 3 + 5 + servers + computers + users);
  const calculatedEdges = Math.round(calculatedNodes * edgeMultiplier);

  // 1. Load Pre-built BloodHound Enterprise Sample
  const handleLoadBloodHoundSample = async () => {
    setBhLoading(true);
    setBhFeedback(null);
    try {
      const res = await fetch('/api/graphs/bloodhound/load-sample', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setBhFeedback(`Successfully loaded CORP.LOCAL Active Directory domain (${data.num_nodes} nodes, ${data.edges ? data.edges.length : 0} edges)!`);
      if (onGraphLoaded) {
        onGraphLoaded(data);
      } else if (onGenerate) {
        onGenerate(data);
      }
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setBhFeedback(`Error loading BloodHound sample: ${err.message}`);
    } finally {
      setBhLoading(false);
    }
  };

  // 2. Ingest Custom BloodHound JSON
  const handleIngestCustomJson = async () => {
    if (!customJson.trim()) return;
    setBhLoading(true);
    setBhFeedback(null);
    try {
      const parsed = JSON.parse(customJson);
      const res = await fetch('/api/graphs/bloodhound/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setBhFeedback(`Successfully ingested custom BloodHound graph (${data.num_nodes} nodes)!`);
      if (onGraphLoaded) {
        onGraphLoaded(data);
      } else if (onGenerate) {
        onGenerate(data);
      }
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setBhFeedback(`Ingestion error: ${err.message}`);
    } finally {
      setBhLoading(false);
    }
  };

  // 3. File Upload Handler for BloodHound JSON
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setCustomJson(event.target.result);
    };
    reader.readAsText(file);
  };

  // 4. Generate Synthetic Topology
  const handleSyntheticSubmit = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    try {
      if (useTargetNodes) {
        await onGenerate({
          scenario_name: scenarioName || `syn_net_${targetNodes}n`,
          target_nodes: Number(targetNodes),
          edge_multiplier: Number(edgeMultiplier),
          cve_probability: Number(cveProb),
          spn_probability: Number(spnProb),
        });
      } else {
        await onGenerate({
          scenario_name: scenarioName || `syn_net_${calculatedNodes}n`,
          num_computers: Number(computers),
          num_servers: Number(servers),
          num_users: Number(users),
          num_ous: Number(ous),
          num_domain_controllers: Number(dcs),
          edge_multiplier: Number(edgeMultiplier),
          cve_probability: Number(cveProb),
          spn_probability: Number(spnProb),
        });
      }
      onClose();
    } catch (err) {
      console.error('Error generating network:', err);
    } finally {
      setIsGenerating(false);
    }
  };

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
        padding: '20px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#09090D',
          border: '1px solid #2B2B38',
          boxShadow: '0 25px 60px rgba(0,0,0,0.95)',
          borderRadius: '12px',
        }}
      >
        {/* Header */}
        <div style={{ padding: '16px 22px', borderBottom: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', background: '#181822', borderRadius: '8px', border: '1px solid #333345' }}>
              <Database size={20} color="#38BDF8" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#FFFFFF' }}>
                Enterprise Network Topology Source
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Select authentic Active Directory BloodHound data or synthesize custom scale
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 10px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', borderBottom: '1px solid #1E1E28', background: '#0D0D14' }}>
          <button
            onClick={() => setActiveTab('BLOODHOUND')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'BLOODHOUND' ? '#14141E' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'BLOODHOUND' ? '2px solid #38BDF8' : 'none',
              color: activeTab === 'BLOODHOUND' ? '#FFFFFF' : '#8E8E9F',
              fontSize: '0.85rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <Database size={16} color={activeTab === 'BLOODHOUND' ? '#38BDF8' : '#8E8E9F'} />
            BloodHound Active Directory
          </button>
          <button
            onClick={() => setActiveTab('SYNTHETIC')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'SYNTHETIC' ? '#14141E' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'SYNTHETIC' ? '2px solid #10B981' : 'none',
              color: activeTab === 'SYNTHETIC' ? '#FFFFFF' : '#8E8E9F',
              fontSize: '0.85rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <Sliders size={16} color={activeTab === 'SYNTHETIC' ? '#10B981' : '#8E8E9F'} />
            Synthetic Topology Synthesizer
          </button>
        </div>

        {/* Tab 1: BloodHound Active Directory */}
        {activeTab === 'BLOODHOUND' && (
          <div style={{ padding: '22px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {/* Enterprise Pre-built Card */}
            <div
              style={{
                padding: '16px',
                background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, rgba(14, 165, 233, 0.02) 100%)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.95rem', fontWeight: '800', color: '#FFFFFF' }}>
                      Production Enterprise Domain (CORP.LOCAL)
                    </span>
                    <span style={{ fontSize: '0.68rem', padding: '2px 6px', background: '#0284C7', color: '#FFFFFF', borderRadius: '4px', fontWeight: '700' }}>
                      SHARPHOUND v4.3
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#94A3B8', marginTop: '4px', lineHeight: '1.4' }}>
                    Authentic multi-tier Active Directory security graph containing Tier-0 Domain Admins, Domain Controllers, SQL database servers, Kerberoastable service accounts, and workstation footholds.
                  </p>
                </div>
              </div>

              {/* Topology Inventory Chips */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
                <div style={{ padding: '8px', background: '#0B132B', borderRadius: '6px', border: '1px solid #1C2541' }}>
                  <span style={{ fontSize: '0.65rem', color: '#64748B' }}>Domain Controllers</span>
                  <div style={{ fontSize: '1rem', fontWeight: '800', color: '#38BDF8' }}>1 (DC01)</div>
                </div>
                <div style={{ padding: '8px', background: '#0B132B', borderRadius: '6px', border: '1px solid #1C2541' }}>
                  <span style={{ fontSize: '0.65rem', color: '#64748B' }}>High Value Admins</span>
                  <div style={{ fontSize: '1rem', fontWeight: '800', color: '#EF4444' }}>Domain Admins</div>
                </div>
                <div style={{ padding: '8px', background: '#0B132B', borderRadius: '6px', border: '1px solid #1C2541' }}>
                  <span style={{ fontSize: '0.65rem', color: '#64748B' }}>Initial Foothold</span>
                  <div style={{ fontSize: '1rem', fontWeight: '800', color: '#F59E0B' }}>WS-FINANCE-01</div>
                </div>
                <div style={{ padding: '8px', background: '#0B132B', borderRadius: '6px', border: '1px solid #1C2541' }}>
                  <span style={{ fontSize: '0.65rem', color: '#64748B' }}>Attack Vector</span>
                  <div style={{ fontSize: '1rem', fontWeight: '800', color: '#10B981' }}>LSASS + RDP</div>
                </div>
              </div>

              <button
                className="btn-cyber btn-primary"
                onClick={handleLoadBloodHoundSample}
                disabled={bhLoading}
                style={{
                  padding: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  fontWeight: '700',
                  fontSize: '0.85rem',
                  background: '#0284C7',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#FFFFFF',
                  cursor: 'pointer',
                }}
              >
                {bhLoading ? <RefreshCw size={16} className="spin" /> : <Database size={16} />}
                Load Enterprise Active Directory Topology
              </button>
            </div>

            {/* Custom BloodHound Ingest Section */}
            <div style={{ borderTop: '1px solid #1E1E28', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#FFFFFF' }}>
                  Custom SharpHound / BloodHound Export Ingest
                </span>
                <label
                  style={{
                    fontSize: '0.75rem',
                    padding: '4px 10px',
                    background: '#1A1A26',
                    border: '1px solid #333345',
                    borderRadius: '4px',
                    color: '#38BDF8',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Upload size={14} />
                  Choose JSON File
                  <input type="file" accept=".json" onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
              </div>

              <textarea
                placeholder='Paste raw BloodHound JSON (e.g. { "data": [ ... ] }) or choose file above...'
                value={customJson}
                onChange={(e) => setCustomJson(e.target.value)}
                rows={5}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#0D0D14',
                  border: '1px solid #222230',
                  borderRadius: '6px',
                  color: '#E2E8F0',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                  outline: 'none',
                  resize: 'vertical',
                }}
              />

              <button
                className="btn-cyber btn-outline"
                onClick={handleIngestCustomJson}
                disabled={bhLoading || !customJson.trim()}
                style={{
                  padding: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  fontWeight: '600',
                  fontSize: '0.8rem',
                }}
              >
                {bhLoading ? <RefreshCw size={14} className="spin" /> : <FileText size={14} />}
                Ingest Custom BloodHound JSON
              </button>
            </div>

            {/* Feedback Message */}
            {bhFeedback && (
              <div
                style={{
                  padding: '10px 14px',
                  background: bhFeedback.includes('Error') ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                  border: `1px solid ${bhFeedback.includes('Error') ? '#EF4444' : '#10B981'}`,
                  borderRadius: '6px',
                  color: bhFeedback.includes('Error') ? '#FCA5A5' : '#6EE7B7',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <CheckCircle2 size={16} />
                {bhFeedback}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Synthetic Topology Synthesizer */}
        {activeTab === 'SYNTHETIC' && (
          <form onSubmit={handleSyntheticSubmit} style={{ padding: '20px 22px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ padding: '12px 14px', background: '#12121A', borderRadius: '8px', border: '1px solid #242430', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', textAlign: 'center' }}>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Target Nodes</span>
                <div style={{ fontSize: '1.15rem', fontWeight: '800', color: '#38BDF8' }}>{calculatedNodes} Nodes</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Target Edges</span>
                <div style={{ fontSize: '1.15rem', fontWeight: '800', color: '#10B981' }}>~{calculatedEdges} Edges</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Edge Density</span>
                <div style={{ fontSize: '1.15rem', fontWeight: '800', color: '#FBBF24' }}>{edgeMultiplier}x / node</div>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px', fontWeight: '600' }}>
                Scenario Identifier
              </label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: '#12121A',
                  border: '1px solid #282836',
                  borderRadius: '6px',
                  color: '#FFFFFF',
                  fontSize: '0.82rem',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className={`btn-cyber ${useTargetNodes ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setUseTargetNodes(true)}
                style={{ flex: 1, padding: '7px', fontSize: '0.78rem', justifyContent: 'center' }}
              >
                Target Node Slider
              </button>
              <button
                type="button"
                className={`btn-cyber ${!useTargetNodes ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setUseTargetNodes(false)}
                style={{ flex: 1, padding: '7px', fontSize: '0.78rem', justifyContent: 'center' }}
              >
                Granular Component Mix
              </button>
            </div>

            {useTargetNodes ? (
              <div style={{ padding: '14px', background: '#12121A', borderRadius: '8px', border: '1px solid #242430' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.82rem', color: '#FFFFFF', fontWeight: '600' }}>Network Scale</span>
                  <span style={{ fontSize: '0.82rem', color: '#38BDF8', fontWeight: '700' }}>{targetNodes} Assets</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="300"
                  step="5"
                  value={targetNodes}
                  onChange={(e) => setTargetNodes(Number(e.target.value))}
                  style={{ width: '100%', accentColor: '#38BDF8' }}
                />
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', padding: '12px', background: '#12121A', borderRadius: '8px', border: '1px solid #242430' }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94A3B8' }}>Workstations: {computers}</label>
                  <input type="range" min="2" max="150" value={computers} onChange={(e) => setComputers(Number(e.target.value))} style={{ width: '100%', accentColor: '#38BDF8' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94A3B8' }}>Servers: {servers}</label>
                  <input type="range" min="1" max="50" value={servers} onChange={(e) => setServers(Number(e.target.value))} style={{ width: '100%', accentColor: '#10B981' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94A3B8' }}>Domain Users: {users}</label>
                  <input type="range" min="2" max="150" value={users} onChange={(e) => setUsers(Number(e.target.value))} style={{ width: '100%', accentColor: '#F59E0B' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94A3B8' }}>Domain Controllers: {dcs}</label>
                  <input type="range" min="1" max="5" value={dcs} onChange={(e) => setDcs(Number(e.target.value))} style={{ width: '100%', accentColor: '#EF4444' }} />
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button
                type="button"
                className="btn-cyber btn-outline"
                onClick={onClose}
                style={{ flex: 1, padding: '10px', fontSize: '0.82rem', justifyContent: 'center' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-cyber btn-primary"
                disabled={isGenerating}
                style={{ flex: 2, padding: '10px', fontSize: '0.82rem', justifyContent: 'center', background: '#10B981', border: 'none' }}
              >
                {isGenerating ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
                Synthesize Topology
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
