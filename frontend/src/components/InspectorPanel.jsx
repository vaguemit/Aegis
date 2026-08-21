import React from 'react';
import { Info, ShieldAlert, Key, Server, Laptop, User, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function InspectorPanel({ selectedNode, onSimulatePatch }) {
  if (!selectedNode) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <Info size={36} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
        <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Asset Inspector</h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '240px' }}>
          Select any node in the enterprise network to inspect Active Directory properties, privileges, and CVE vulnerabilities.
        </p>
      </div>
    );
  }

  const getEntityIcon = (type) => {
    switch (type) {
      case 'DomainController':
      case 'Domain':
        return <Server size={18} color="#8B5CF6" />;
      case 'Server':
        return <Server size={18} color="#0284C7" />;
      case 'Computer':
        return <Laptop size={18} color="#3B82F6" />;
      case 'User':
        return <User size={18} color="#10B981" />;
      default:
        return <Key size={18} color="#F59E0B" />;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '18px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Node Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
            {getEntityIcon(selectedNode.entity_type)}
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#FFFFFF' }}>{selectedNode.name}</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              Node #{selectedNode.index} • {selectedNode.entity_type}
            </span>
          </div>
        </div>

        {selectedNode.is_vulnerable && (
          <span className="badge badge-amber">
            <AlertTriangle size={12} /> Vulnerable
          </span>
        )}
      </div>

      {/* Security Roles & Status Flags */}
      <div>
        <h4 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '8px' }}>
          Active Directory Security Properties
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Compromised</span>
            {selectedNode.is_owned ? (
              <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>Initial Foothold</span>
            ) : (
              <XCircle size={14} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Crown Jewel</span>
            {selectedNode.is_target || selectedNode.is_high_value ? (
              <span className="badge badge-rose" style={{ fontSize: '0.7rem' }}>High Value</span>
            ) : (
              <XCircle size={14} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Service SPN</span>
            {selectedNode.has_spn ? (
              <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>Kerberoastable</span>
            ) : (
              <XCircle size={14} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Status</span>
            {selectedNode.is_enabled ? (
              <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>Enabled</span>
            ) : (
              <span className="badge badge-rose" style={{ fontSize: '0.7rem' }}>Disabled</span>
            )}
          </div>
        </div>
      </div>

      {/* Vulnerability Mitigation Trigger */}
      {selectedNode.is_vulnerable && (
        <div style={{ padding: '12px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <ShieldAlert size={16} color="#F59E0B" />
            <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#FBBF24' }}>Unpatched CVE Exploit Detected</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            This asset contains remote code execution vulnerabilities permitting lateral movement via SMB/RPC.
          </p>
          <button
            className="btn-cyber btn-success"
            style={{ width: '100%', fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={() => onSimulatePatch(selectedNode.index)}
          >
            <CheckCircle2 size={14} />
            Simulate Patching Vulnerability
          </button>
        </div>
      )}
    </div>
  );
}
