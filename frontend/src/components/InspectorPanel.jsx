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
  Building,
  Wifi,
} from 'lucide-react';

export default function InspectorPanel({
  selectedNode,
  onSimulatePatch,
  onSetSource,
  onSetTarget,
}) {
  if (!selectedNode) {
    return (
      <div style={{ padding: '24px 16px', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Server size={32} color="var(--text-muted)" style={{ marginBottom: '10px' }} />
        <h4 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-secondary)', margin: 0 }}>Asset Inspector</h4>
        <p style={{ fontSize: '0.74rem', marginTop: '4px', maxWidth: '220px' }}>
          Click on any node in the network canvas to view its department, assigned user, CVEs, and security posture.
        </p>
      </div>
    );
  }

  const lowerName = selectedNode.name.toLowerCase();
  let deptTitle = 'Corporate Network';
  let deptIcon = '🏢';
  let subnetIP = `192.168.10.${selectedNode.index + 10}`;

  if (lowerName.includes('hr')) {
    deptTitle = 'Human Resources (HR Dept)';
    deptIcon = '👥';
    subnetIP = `192.168.20.${selectedNode.index + 10} (VLAN 20 - HR)`;
  } else if (lowerName.includes('finance') || lowerName.includes('payroll') || lowerName.includes('payment')) {
    deptTitle = 'Finance & Accounting';
    deptIcon = '💰';
    subnetIP = `192.168.30.${selectedNode.index + 10} (VLAN 30 - Finance)`;
  } else if (lowerName.includes('engineering') || lowerName.includes('dev') || lowerName.includes('gitlab')) {
    deptTitle = 'Engineering & DevOps';
    deptIcon = '⚙️';
    subnetIP = `192.168.40.${selectedNode.index + 10} (VLAN 40 - Dev)`;
  } else if (lowerName.includes('exec') || lowerName.includes('leadership')) {
    deptTitle = 'Executive Leadership Suite';
    deptIcon = '👔';
    subnetIP = `192.168.50.${selectedNode.index + 10} (VLAN 50 - Exec)`;
  } else if (lowerName.includes('sales') || lowerName.includes('marketing')) {
    deptTitle = 'Sales & Marketing';
    deptIcon = '📈';
    subnetIP = `192.168.60.${selectedNode.index + 10} (VLAN 60 - Sales)`;
  } else if (lowerName.includes('dc') || lowerName.includes('domain')) {
    deptTitle = 'Identity Core (Domain Controller)';
    deptIcon = '👑';
    subnetIP = `10.0.0.1 (Core DC Subnet)`;
  } else if (lowerName.includes('server') || lowerName.includes('sql') || lowerName.includes('web') || lowerName.includes('database')) {
    deptTitle = 'Production Datacenter Server';
    deptIcon = '🌐';
    subnetIP = `172.16.10.${selectedNode.index + 10} (DMZ Server Farm)`;
  }

  return (
    <div style={{ padding: '14px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Asset Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid #1E1E28', paddingBottom: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '1.1rem' }}>{deptIcon}</span>
            <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF', margin: 0 }}>{selectedNode.name}</h3>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#38BDF8', fontWeight: '600', marginTop: '2px', display: 'block' }}>
            {deptTitle}
          </span>
        </div>

        {selectedNode.is_vulnerable && (
          <span className="badge badge-amber" style={{ fontSize: '0.66rem' }}>
            <AlertTriangle size={10} /> Unpatched CVE
          </span>
        )}
      </div>

      {/* Quick Action Buttons: Set as Foothold or Crown Jewel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
        <button
          className="btn-cyber btn-outline"
          onClick={() => onSetSource && onSetSource(selectedNode.index)}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
          title="Set this machine as the initial adversary breach foothold"
        >
          <Crosshair size={12} color="#38BDF8" /> Set as Foothold
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => onSetTarget && onSetTarget(selectedNode.index)}
          style={{ padding: '5px 8px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
          title="Set this machine as the destination crown jewel target"
        >
          <Target size={12} color="#F43F5E" /> Set as Target
        </button>
      </div>

      {/* Network Subnet & IP Info */}
      <div style={{ padding: '7px 9px', background: '#12121A', borderRadius: '6px', border: '1px solid #1E1E28', fontSize: '0.72rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Department:</span>
          <span style={{ color: '#FFFFFF', fontWeight: '600' }}>{deptTitle}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
          <span style={{ color: 'var(--text-muted)' }}>IP / Subnet:</span>
          <code style={{ color: '#38BDF8' }}>{subnetIP}</code>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Operating System:</span>
          <span style={{ color: '#FFFFFF' }}>{selectedNode.os || 'Windows 11 Enterprise'}</span>
        </div>
      </div>

      {/* Security Status Flags */}
      <div>
        <h4 style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '5px' }}>
          Security Posture
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
          <div style={{ padding: '5px 8px', background: '#12121A', borderRadius: '5px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Compromised</span>
            {selectedNode.is_owned ? (
              <span className="badge badge-cyan" style={{ fontSize: '0.62rem' }}>Foothold</span>
            ) : (
              <XCircle size={12} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '5px 8px', background: '#12121A', borderRadius: '5px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Crown Jewel</span>
            {selectedNode.is_target || selectedNode.is_high_value ? (
              <span className="badge badge-rose" style={{ fontSize: '0.62rem' }}>Target</span>
            ) : (
              <XCircle size={12} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '5px 8px', background: '#12121A', borderRadius: '5px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SPN Service</span>
            {selectedNode.has_spn ? (
              <span className="badge badge-purple" style={{ fontSize: '0.62rem' }}>Kerberoast</span>
            ) : (
              <XCircle size={12} color="var(--text-muted)" />
            )}
          </div>

          <div style={{ padding: '5px 8px', background: '#12121A', borderRadius: '5px', border: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Network State</span>
            {selectedNode.is_enabled ? (
              <span className="badge badge-emerald" style={{ fontSize: '0.62rem' }}>Online</span>
            ) : (
              <span className="badge badge-rose" style={{ fontSize: '0.62rem' }}>Isolated</span>
            )}
          </div>
        </div>
      </div>

      {/* Vulnerability Mitigation Trigger */}
      {selectedNode.is_vulnerable && (
        <div style={{ padding: '8px 10px', background: '#16130B', borderRadius: '6px', border: '1px solid #332712' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
            <ShieldAlert size={13} color="#F59E0B" />
            <span style={{ fontSize: '0.74rem', fontWeight: '700', color: '#FBBF24' }}>Unpatched CVE Exploit</span>
          </div>
          <p style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '6px', lineHeight: 1.3 }}>
            Exposed service allows remote lateral movement.
          </p>
          <button
            className="btn-cyber"
            style={{ width: '100%', fontSize: '0.72rem', background: '#F59E0B', color: '#000000', fontWeight: '800', padding: '5px 8px' }}
            onClick={() => onSimulatePatch(selectedNode.index)}
          >
            Simulate Patching Vulnerability
          </button>
        </div>
      )}
    </div>
  );
}
