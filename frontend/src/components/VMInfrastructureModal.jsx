import React, { useState, useEffect } from 'react';
import { Server, HardDrive, Cpu, ShieldAlert, CheckCircle2, AlertTriangle, Network, X } from 'lucide-react';

export default function VMInfrastructureModal({ isOpen, onClose, graphId }) {
  const [vmData, setVmData] = useState(null);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    if (!isOpen || !graphId) return;

    fetch(`/api/simulation/vms/${graphId}`)
      .then((res) => res.json())
      .then((data) => setVmData(data))
      .catch((err) => console.error('Error fetching VM data:', err));
  }, [isOpen, graphId]);

  if (!isOpen) return null;

  const vms = vmData?.virtual_machines || [];
  const filteredVms = filter === 'ALL' ? vms : (filter === 'VULN' ? vms.filter(v => v.cves.length > 0) : vms.filter(v => v.is_crown_jewel));

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
        padding: '24px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '950px',
          maxHeight: '85vh',
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
              <Server size={20} color="#FFFFFF" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#FFFFFF' }}>
                Virtual Machine Infrastructure Cluster
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Simulated Hypervisors (VMware ESXi 8.0 / Proxmox VE) & Virtual Network Segments
              </span>
            </div>
          </div>

          <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 10px' }}>
            <X size={16} />
          </button>
        </div>

        {/* Hypervisor Host Summary Cards */}
        {vmData?.hypervisor_hosts && (
          <div style={{ padding: '14px 22px', background: '#0F0F16', borderBottom: '1px solid #1E1E28', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {vmData.hypervisor_hosts.map((h, i) => (
              <div key={i} style={{ padding: '10px 12px', background: '#161620', borderRadius: '8px', border: '1px solid #2A2A3A' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '2px' }}>
                  {h.host_name.split('.')[0]}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{h.type}</div>
                <div style={{ fontSize: '0.72rem', color: '#38BDF8', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
                  {h.vm_count} VMs • {h.cpu_cores} vCPUs • {h.ram_gb} GB RAM
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Filter Controls */}
        <div style={{ padding: '10px 22px', background: '#09090D', borderBottom: '1px solid #1E1E28', display: 'flex', gap: '8px' }}>
          <button
            className="btn-cyber"
            onClick={() => setFilter('ALL')}
            style={{
              padding: '4px 12px',
              fontSize: '0.75rem',
              background: filter === 'ALL' ? '#FFFFFF' : '#14141C',
              color: filter === 'ALL' ? '#000000' : 'var(--text-secondary)',
            }}
          >
            All VMs ({vms.length})
          </button>
          <button
            className="btn-cyber"
            onClick={() => setFilter('VULN')}
            style={{
              padding: '4px 12px',
              fontSize: '0.75rem',
              background: filter === 'VULN' ? '#F59E0B' : '#14141C',
              color: filter === 'VULN' ? '#000000' : '#FBBF24',
            }}
          >
            Vulnerable CVE Hosts
          </button>
          <button
            className="btn-cyber"
            onClick={() => setFilter('CROWN')}
            style={{
              padding: '4px 12px',
              fontSize: '0.75rem',
              background: filter === 'CROWN' ? '#EC4899' : '#14141C',
              color: filter === 'CROWN' ? '#FFFFFF' : '#F472B6',
            }}
          >
            Crown Jewels
          </button>
        </div>

        {/* VM Instances Table */}
        <div style={{ padding: '20px 22px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #222230', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px' }}>VM Instance</th>
                <th style={{ padding: '8px' }}>Operating System</th>
                <th style={{ padding: '8px' }}>IP / Subnet</th>
                <th style={{ padding: '8px' }}>Hardware</th>
                <th style={{ padding: '8px' }}>Open Ports</th>
                <th style={{ padding: '8px' }}>CVE Vulnerabilities</th>
                <th style={{ padding: '8px' }}>Privilege</th>
              </tr>
            </thead>
            <tbody>
              {filteredVms.map((v, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #181824' }}>
                  <td style={{ padding: '8px', fontWeight: '600', color: '#FFFFFF' }}>{v.vm_name}</td>
                  <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{v.os}</td>
                  <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>{v.ip}</td>
                  <td style={{ padding: '8px', fontFamily: 'var(--font-mono)' }}>{v.cpu_cores}c / {v.ram_gb}G</td>
                  <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', color: '#94A3B8' }}>{v.open_ports.join(', ')}</td>
                  <td style={{ padding: '8px' }}>
                    {v.cves.length > 0 ? (
                      <span className="badge badge-amber" style={{ fontSize: '0.68rem' }}>
                        {v.cves[0]}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None (Secured)</span>
                    )}
                  </td>
                  <td style={{ padding: '8px' }}>
                    <span className={`badge ${v.privilege === 'SYSTEM' ? 'badge-purple' : 'badge-obsidian'}`} style={{ fontSize: '0.68rem' }}>
                      {v.privilege}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
