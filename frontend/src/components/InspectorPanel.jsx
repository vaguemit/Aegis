import React from 'react';
import {
  Server,
  Shield,
  AlertTriangle,
  Layers,
  Terminal,
  Activity,
  XCircle,
  ShieldAlert,
  ShieldCheck,
  CheckCircle,
  Crosshair,
  Target,
} from 'lucide-react';

export default function InspectorPanel({
  selectedNode,
  onSimulatePatch,
  onSetSource,
  onSetTarget,
}) {
  if (!selectedNode) {
    return (
      <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', background: '#09090D', border: '1px solid #1E1E28' }}>
        <Server size={36} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
        <h4 style={{ fontSize: '0.92rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Asset Inspector</h4>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '220px' }}>
          Click on any node in the network graph canvas to inspect its security posture, CVE exploits, and virtual machine hardware.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '16px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#09090D', border: '1px solid #1E1E28' }}>
      {/* Asset Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid #1E1E28', paddingBottom: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Server size={16} color="#38BDF8" />
            <h3 style={{ fontSize: '0.96rem', fontWeight: '700', color: '#FFFFFF' }}>{selectedNode.name}</h3>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Asset ID: {selectedNode.id} • Node #{selectedNode.index}
          </span>
        </div>

        {selectedNode.is_vulnerable && (
          <span className="badge badge-amber" style={{ fontSize: '0.68rem' }}>
            <AlertTriangle size={11} /> CVE Exploit
          </span>
        )}
      </div>

      {/* Quick Action Buttons: Set as Foothold or Crown Jewel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
        <button
          className="btn-cyber btn-outline"
          onClick={() => onSetSource && onSetSource(selectedNode.index)}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
          title="Set this asset as the initial adversary breach origin and re-predict attack trajectory"
        >
          <Crosshair size={12} color="#38BDF8" /> Set as Foothold
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => onSetTarget && onSetTarget(selectedNode.index)}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
          title="Set this asset as the crown jewel target and re-predict attack trajectory"
        >
          <Target size={12} color="#F43F5E" /> Set as Target
        </button>
      </div>

      {/* Security Roles & Status Flags */}
      <div>
        <h4 style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Security & Identity Status
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Compromised</span>
            {selectedNode.is_owned ? (
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>Foothold</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Crown Jewel</span>
            {selectedNode.is_target || selectedNode.is_high_value ? (
              <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>High Value</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>SPN Service</span>
            {selectedNode.has_spn ? (
              <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>Kerberoast</span>
            ) : (
              <XCircle size={13} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '6px 10px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Status</span>
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
            Vulnerable to remote exploit allowing adversary lateral movement.
          </p>
          <button
            className="btn-cyber"
            style={{ width: '100%', fontSize: '0.74rem', background: '#F59E0B', color: '#000000', fontWeight: '700', padding: '6px 10px' }}
            onClick={() => onSimulatePatch(selectedNode.index)}
          >
            Simulate Patching Vulnerability
          </button>
        </div>
      )}

      {/* Hardware & OS Specifications */}
      <div>
        <h4 style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Asset Specifications
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.74rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', background: '#12121A', borderRadius: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Entity Type:</span>
            <span style={{ color: '#FFFFFF', fontWeight: '600' }}>{selectedNode.entity_type}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', background: '#12121A', borderRadius: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Operating System:</span>
            <span style={{ color: '#FFFFFF' }}>{selectedNode.os || 'Windows 11 / Server 2022'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
