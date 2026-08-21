import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, Layers, Network, ShieldAlert, Cpu, Sparkles, X } from 'lucide-react';

export default function ScenarioModal({ isOpen, onClose, onGenerate }) {
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

  // Sync detailed controls when targetNodes changes
  useEffect(() => {
    if (useTargetNodes) {
      const overhead = 1 + dcs + ous + 3 + 5; // domain + dcs + ous + gpos + groups
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

  const handleSubmit = async (e) => {
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
          maxWidth: '620px',
          maxHeight: '90vh',
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
              <Sliders size={20} color="#FFFFFF" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#FFFFFF' }}>
                Synthesize Enterprise Topology
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Fine-Grained Node & Edge Count Density Synthesizer
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 10px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '20px 22px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Estimated Topology Metrics Banner */}
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

          {/* Scenario Name */}
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
              required
            />
          </div>

          {/* Target Node Count Control */}
          <div style={{ padding: '14px', background: '#101016', borderRadius: '8px', border: '1px solid #20202C' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: '700', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={15} color="#38BDF8" /> Total Node Count: {targetNodes} Nodes
              </label>
              <span className="badge badge-obsidian" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                {targetNodes} Nodes
              </span>
            </div>

            <input
              type="range"
              min="15"
              max="500"
              step="5"
              value={targetNodes}
              onChange={(e) => setTargetNodes(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#38BDF8', cursor: 'pointer' }}
            />

            {/* Quick Node Presets */}
            <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
              {[20, 50, 100, 250, 500].map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setTargetNodes(preset)}
                  className="btn-cyber btn-outline"
                  style={{
                    flex: 1,
                    padding: '3px 0',
                    fontSize: '0.72rem',
                    background: targetNodes === preset ? '#FFFFFF' : '#161622',
                    color: targetNodes === preset ? '#000000' : 'var(--text-secondary)',
                  }}
                >
                  {preset} Nodes
                </button>
              ))}
            </div>
          </div>

          {/* Edge Density / Multiplier Control */}
          <div style={{ padding: '14px', background: '#101016', borderRadius: '8px', border: '1px solid #20202C' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: '700', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Network size={15} color="#10B981" /> Edge Connectivity Multiplier: {edgeMultiplier}x
              </label>
              <span className="badge badge-obsidian" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                ~{calculatedEdges} Edges
              </span>
            </div>

            <input
              type="range"
              min="1.5"
              max="7.0"
              step="0.5"
              value={edgeMultiplier}
              onChange={(e) => setEdgeMultiplier(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#10B981', cursor: 'pointer' }}
            />

            {/* Quick Edge Presets */}
            <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
              {[
                { label: 'Sparse (2.0x)', val: 2.0 },
                { label: 'Standard (3.5x)', val: 3.5 },
                { label: 'Dense (5.0x)', val: 5.0 },
                { label: 'Ultra (6.5x)', val: 6.5 },
              ].map((p) => (
                <button
                  key={p.val}
                  type="button"
                  onClick={() => setEdgeMultiplier(p.val)}
                  className="btn-cyber btn-outline"
                  style={{
                    flex: 1,
                    padding: '3px 0',
                    fontSize: '0.72rem',
                    background: edgeMultiplier === p.val ? '#10B981' : '#161622',
                    color: edgeMultiplier === p.val ? '#000000' : 'var(--text-secondary)',
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Vulnerabilities and SPN Probability */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ padding: '10px 12px', background: '#101016', borderRadius: '6px', border: '1px solid #1E1E28' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                CVE Vulnerability Rate ({(cveProb * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={cveProb}
                onChange={(e) => setCveProb(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#F59E0B' }}
              />
            </div>

            <div style={{ padding: '10px 12px', background: '#101016', borderRadius: '6px', border: '1px solid #1E1E28' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Kerberoast SPN Rate ({(spnProb * 100).toFixed(0)}%)
              </label>
              <input
                type="range"
                min="0.05"
                max="0.40"
                step="0.05"
                value={spnProb}
                onChange={(e) => setSpnProb(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#A855F7' }}
              />
            </div>
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            className="btn-cyber btn-primary"
            disabled={isGenerating}
            style={{ width: '100%', padding: '10px', fontSize: '0.88rem', marginTop: '4px' }}
          >
            {isGenerating ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
            Synthesize {calculatedNodes} Nodes & ~{calculatedEdges} Edges
          </button>
        </form>
      </div>
    </div>
  );
}
