import React from 'react';
import { Info, ShieldAlert, Key, Server, Laptop, User, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function InspectorPanel({ selectedNode, onSimulatePatch }) {
  if (!selectedNode) {
    return (
      <div className="glass-panel" style={{ padding: '16px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', background: '#09090D', border: '1px solid #1E1E28' }}>
        <Info size={30} color="var(--text-muted)" style={{ marginBottom: '10px' }} />
        <h4 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Asset & VM Inspector</h4>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '220px' }}>
          Select any node in the enterprise network to inspect Active Directory properties, privileges, and CVE vulnerabilities.
        </p>
      </div>
    );
  }

  const getEntityIcon = (type) => {
    switch (type) {
      case 'DomainController':
      case 'Domain':
        return <Server size={16} color="#C084FC" />;
      case 'Server':
        return <Server size={16} color="#38BDF8" />;
      case 'Computer':
        return <Laptop size={16} color="#60A5FA" />;
      case 'User':
        return <User size={16} color="#34D399" />;
      default:
        return <Key size={16} color="#FBBF24" />;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Node Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1F1F2A', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ padding: '6px', background: '#161620', borderRadius: '6px', border: '1px solid #282836' }}>
            {getEntityIcon(selectedNode.entity_type)}
          </div>
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF' }}>{selectedNode.name}</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Node #{selectedNode.index} • {selectedNode.entity_type}
            </span>
          </div>
        </div>

        {selectedNode.is_vulnerable && (
          <span className="badge badge-amber" style={{ fontSize: '0.68rem' }}>
            <AlertTriangle size={11} /> CVE Exploit
          </span>
        )}
      </div>

      {/* Security Roles & Status Flags */}
      <div>
        <h4 style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Security & Identity Configuration
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Compromised</span>
            {selectedNode.is_owned ? (
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>Foothold</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Crown Jewel</span>
            {selectedNode.is_target || selectedNode.is_high_value ? (
              <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>High Value</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>SPN Service</span>
            {selectedNode.has_spn ? (
              <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>Kerberoast</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>Status</span>
            {selectedNode.is_enabled ? (
              <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>Enabled</span>
            ) : (
              <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>Disabled</span>
            )}
          </div>
        </div>
      </div>

      {/* Vulnerability Mitigation Trigger */}
      {selectedNode.is_vulnerable && (
        <div style={{ padding: '10px 12px', background: '#16130B', borderRadius: '6px', border: '1px solid #332712' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <ShieldAlert size={14} color="#F59E0B" />
            <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#FBBF24' }}>Unpatched CVE Exploit</span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Vulnerable to remote exploitation allowing lateral movement.
          </p>
          <button
            className="btn-cyber btn-success"
            style={{ width: '100%', fontSize: '0.74rem', padding: '5px 10px' }}
            onClick={() => onSimulatePatch(selectedNode.index)}
          >
            <CheckCircle2 size={13} />
            Simulate Patching Vulnerability
          </button>
        </div>
      )}
    </div>
  );
}
