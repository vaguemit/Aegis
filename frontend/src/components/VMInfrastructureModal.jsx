import React, { useState, useEffect } from 'react';
import { Server, HardDrive, Cpu, ShieldAlert, CheckCircle2, AlertTriangle, Network, X, RefreshCw, Zap, Camera, Skull, Activity, ShieldCheck } from 'lucide-react';

export default function VMInfrastructureModal({ isOpen, onClose, graphId }) {
  const [activeTab, setActiveTab] = useState('VMWARE_LIVE'); // 'VMWARE_LIVE' or 'CLUSTER_SIM'
  const [vmData, setVmData] = useState(null);
  const [vmwareStatus, setVmwareStatus] = useState(null);
  const [vmwareInventory, setVmwareInventory] = useState(null);
  const [rogueFindings, setRogueFindings] = useState([]);
  const [telemetryEvents, setTelemetryEvents] = useState([]);
  const [actionLoading, setActionLoading] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    if (!isOpen) return;

    // Fetch simulation data
    if (graphId) {
      fetch(`/api/simulation/vms/${graphId}`)
        .then((res) => res.json())
        .then((data) => setVmData(data))
        .catch((err) => console.error('Error fetching VM data:', err));
    }

    // Fetch VMware Live data
    fetchVmwareState();
  }, [isOpen, graphId]);

  const fetchVmwareState = () => {
    fetch('/api/vmware/status')
      .then(res => res.json())
      .then(data => setVmwareStatus(data))
      .catch(err => console.error(err));

    fetch('/api/vmware/inventory')
      .then(res => res.json())
      .then(data => setVmwareInventory(data))
      .catch(err => console.error(err));

    fetch('/api/vmware/rogue-vms')
      .then(res => res.json())
      .then(data => setRogueFindings(data))
      .catch(err => console.error(err));

    fetch('/api/vmware/events?limit=8')
      .then(res => res.json())
      .then(data => setTelemetryEvents(data))
      .catch(err => console.error(err));
  };

  const handleQuarantine = async (vmId) => {
    setActionLoading(`quarantine-${vmId}`);
    try {
      const res = await fetch('/api/vmware/quarantine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vm_id: vmId, method: 'PORTGROUP_MIGRATION', quarantine_portgroup: 'Quarantine_VLAN_999' }),
      });
      const data = await res.json();
      setActionFeedback(`VM ${vmId} placed in isolated VLAN 999`);
      fetchVmwareState();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSnapshot = async (vmId) => {
    setActionLoading(`snap-${vmId}`);
    try {
      const res = await fetch('/api/vmware/snapshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vm_id: vmId, include_memory: true }),
      });
      const data = await res.json();
      setActionFeedback(`Forensic snapshot with RAM dump captured for ${vmId}`);
      fetchVmwareState();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleKillRogue = async (vmId) => {
    setActionLoading(`kill-${vmId}`);
    try {
      const res = await fetch('/api/vmware/guest-ops/terminate-rogue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vm_id: vmId }),
      });
      const data = await res.json();
      setActionFeedback(`Terminated rogue reverse tunnel processes in ${vmId}`);
      fetchVmwareState();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSyncGraph = async () => {
    setActionLoading('sync-graph');
    try {
      const res = await fetch('/api/vmware/sync-graph', { method: 'POST' });
      const data = await res.json();
      setActionFeedback(`Live VMware cluster synchronized into AegisPath graph (${data.num_nodes} nodes)!`);
      if (onClose) setTimeout(onClose, 1200);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  if (!isOpen) return null;

  const vms = vmData?.virtual_machines || [];
  const liveVms = vmwareInventory?.vms || [];

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.88)',
        backdropFilter: 'blur(14px)',
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
          maxWidth: '1080px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#09090D',
          border: '1px solid #2B2B38',
          boxShadow: '0 30px 80px rgba(0,0,0,0.98)',
        }}
      >
        {/* Header */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #1E1E28', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0D0D14' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '10px', background: '#1A1A26', borderRadius: '8px', border: '1px solid #36364A' }}>
              <Server size={22} color="#38BDF8" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#FFFFFF' }}>
                  Enterprise VMware vSphere & Hypervisor Command Center
                </h2>
                <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>
                  ESXi 8.0 Live
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Real-world hypervisor telemetry, outsider detection, forensic memory capture & active network quarantine
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button className="btn-cyber btn-outline" onClick={handleSyncGraph} disabled={actionLoading === 'sync-graph'} style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RefreshCw size={14} className={actionLoading === 'sync-graph' ? 'spin' : ''} />
              Sync vSphere to Graph
            </button>
            <button className="btn-cyber btn-outline" onClick={onClose} style={{ padding: '6px 10px' }}>
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', background: '#09090D', borderBottom: '1px solid #1E1E28', padding: '0 24px' }}>
          <button
            onClick={() => setActiveTab('VMWARE_LIVE')}
            style={{
              padding: '12px 18px',
              fontSize: '0.82rem',
              fontWeight: '600',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'VMWARE_LIVE' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'VMWARE_LIVE' ? '#38BDF8' : 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Activity size={16} />
            Live vSphere Operations & Outsider Defense
          </button>
          <button
            onClick={() => setActiveTab('CLUSTER_SIM')}
            style={{
              padding: '12px 18px',
              fontSize: '0.82rem',
              fontWeight: '600',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'CLUSTER_SIM' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'CLUSTER_SIM' ? '#38BDF8' : 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <HardDrive size={16} />
            AD Graph VM Mapping View
          </button>
        </div>

        {/* Action Feedback Banner */}
        {actionFeedback && (
          <div style={{ padding: '8px 24px', background: 'rgba(16, 185, 129, 0.15)', borderBottom: '1px solid #10B981', color: '#10B981', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={15} />
            {actionFeedback}
          </div>
        )}

        {/* Main Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {activeTab === 'VMWARE_LIVE' ? (
            <div>
              {/* ESXi Bare-Metal Cluster Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '20px' }}>
                <div style={{ padding: '14px', background: '#12121A', borderRadius: '8px', border: '1px solid #232332' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hypervisor Cluster</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                    {vmwareInventory?.cluster_name || 'Cluster-Production'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#38BDF8', marginTop: '4px' }}>
                    vCenter: {vmwareStatus?.host || 'vcenter.corp.internal'}
                  </div>
                </div>

                <div style={{ padding: '14px', background: '#12121A', borderRadius: '8px', border: '1px solid #232332' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>ESXi Bare-Metal Hosts</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                    {vmwareInventory?.total_hosts || 2} Connected Nodes
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#10B981', marginTop: '4px' }}>
                    128 vCPUs • 1,024 GB RAM Allocated
                  </div>
                </div>

                <div style={{ padding: '14px', background: rogueFindings.length > 0 ? 'rgba(239, 68, 68, 0.1)' : '#12121A', borderRadius: '8px', border: rogueFindings.length > 0 ? '1px solid #EF4444' : '1px solid #232332' }}>
                  <div style={{ fontSize: '0.72rem', color: rogueFindings.length > 0 ? '#EF4444' : 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldAlert size={14} />
                    Outsider Threats Detected
                  </div>
                  <div style={{ fontSize: '1.05rem', fontWeight: '700', color: rogueFindings.length > 0 ? '#F87171' : '#FFFFFF', marginTop: '2px' }}>
                    {rogueFindings.length} Rogue / Shadow VMs
                  </div>
                  <div style={{ fontSize: '0.75rem', color: rogueFindings.length > 0 ? '#FCA5A5' : 'var(--text-muted)', marginTop: '4px' }}>
                    {rogueFindings.length > 0 ? 'Immediate vNIC Quarantine Recommended' : 'Perimeter Clean'}
                  </div>
                </div>
              </div>

              {/* Rogue Outsider Threat Section */}
              {rogueFindings.length > 0 && (
                <div style={{ marginBottom: '20px', padding: '16px', background: 'rgba(239, 68, 68, 0.06)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <AlertTriangle color="#EF4444" size={18} />
                    <h3 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#FFFFFF' }}>
                      Active Outsider Nodes & Covert Tunnel Alerts
                    </h3>
                  </div>

                  {rogueFindings.map((rf, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: '#13131D', borderRadius: '6px', border: '1px solid #28283A', marginBottom: '8px' }}>
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#F87171', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{rf.vm_name}</span>
                          <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>{rf.guest_os}</span>
                          <span style={{ fontSize: '0.72rem', color: '#38BDF8', fontFamily: 'var(--font-mono)' }}>IP: {rf.ip_address}</span>
                        </div>
                        <div style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          {rf.risk_indicators.join(' • ')}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="btn-cyber"
                          onClick={() => handleQuarantine(rf.vm_name)}
                          disabled={actionLoading === `quarantine-${rf.vm_name}`}
                          style={{ fontSize: '0.72rem', background: '#EF4444', color: '#FFFFFF', padding: '6px 12px' }}
                        >
                          <ShieldAlert size={13} style={{ marginRight: '4px' }} />
                          Quarantine VLAN 999
                        </button>
                        <button
                          className="btn-cyber btn-outline"
                          onClick={() => handleKillRogue(rf.vm_name)}
                          disabled={actionLoading === `kill-${rf.vm_name}`}
                          style={{ fontSize: '0.72rem', padding: '6px 10px' }}
                        >
                          <Skull size={13} style={{ marginRight: '4px' }} />
                          Kill chisel.exe
                        </button>
                        <button
                          className="btn-cyber btn-outline"
                          onClick={() => handleSnapshot(rf.vm_name)}
                          disabled={actionLoading === `snap-${rf.vm_name}`}
                          style={{ fontSize: '0.72rem', padding: '6px 10px' }}
                        >
                          <Camera size={13} style={{ marginRight: '4px' }} />
                          Dump RAM
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Live Virtual Machines Table */}
              <div style={{ background: '#101017', borderRadius: '8px', border: '1px solid #1E1E28', padding: '16px', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '12px' }}>
                  Live Virtual Machine Inventory & Hypervisor Actions
                </h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #222230', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px' }}>Virtual Machine</th>
                      <th style={{ padding: '8px' }}>Guest Operating System</th>
                      <th style={{ padding: '8px' }}>IP / Portgroup</th>
                      <th style={{ padding: '8px' }}>VLAN</th>
                      <th style={{ padding: '8px' }}>Status</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Active Defense Controls</th>
                    </tr>
                  </thead>
                  <tbody>
                    {liveVms.map((vm, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #161622' }}>
                        <td style={{ padding: '8px', fontWeight: '600', color: vm.is_outsider ? '#F87171' : '#FFFFFF' }}>
                          {vm.name}
                        </td>
                        <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{vm.guest_os}</td>
                        <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>
                          {vm.ip_address} <span style={{ color: 'var(--text-muted)' }}>({vm.portgroup})</span>
                        </td>
                        <td style={{ padding: '8px', fontFamily: 'var(--font-mono)' }}>VLAN {vm.vlan_id}</td>
                        <td style={{ padding: '8px' }}>
                          {vm.is_isolated ? (
                            <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>QUARANTINED</span>
                          ) : (
                            <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>ONLINE</span>
                          )}
                        </td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                            <button
                              className="btn-cyber btn-outline"
                              onClick={() => handleSnapshot(vm.name)}
                              style={{ padding: '4px 8px', fontSize: '0.68rem' }}
                            >
                              <Camera size={12} style={{ marginRight: '3px' }} />
                              Snap
                            </button>
                            {vm.is_isolated ? (
                              <button
                                className="btn-cyber"
                                onClick={() => {
                                  fetch('/api/vmware/restore', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ vm_id: vm.name, target_portgroup: 'Workstations-VLAN500', vlan_id: 500 }),
                                  }).then(() => fetchVmwareState());
                                }}
                                style={{ padding: '4px 8px', fontSize: '0.68rem', background: '#10B981', color: '#FFFFFF' }}
                              >
                                Restore
                              </button>
                            ) : (
                              <button
                                className="btn-cyber"
                                onClick={() => handleQuarantine(vm.name)}
                                style={{ padding: '4px 8px', fontSize: '0.68rem', background: '#EF4444', color: '#FFFFFF' }}
                              >
                                Isolate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Hypervisor Syslog & Audit Stream */}
              <div style={{ background: '#09090E', borderRadius: '8px', border: '1px solid #1C1C26', padding: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Activity size={15} color="#38BDF8" />
                  <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#FFFFFF' }}>
                    Live VMware Event Stream & Syslog
                  </span>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {telemetryEvents.map((ev, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px' }}>
                      <span style={{ color: '#475569' }}>[{ev.timestamp.split('T')[1].slice(0,8)}]</span>
                      <span style={{ color: ev.severity === 'CRITICAL' ? '#F87171' : (ev.severity === 'WARNING' ? '#FBBF24' : '#38BDF8') }}>
                        {ev.event_type}:
                      </span>
                      <span>{ev.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Simulation View */
            <div>
              <div style={{ padding: '10px 0', display: 'flex', gap: '8px', marginBottom: '14px' }}>
                <button
                  className="btn-cyber"
                  onClick={() => setFilter('ALL')}
                  style={{ padding: '4px 12px', fontSize: '0.75rem', background: filter === 'ALL' ? '#FFFFFF' : '#14141C', color: filter === 'ALL' ? '#000000' : 'var(--text-secondary)' }}
                >
                  All Graph Nodes ({vms.length})
                </button>
                <button
                  className="btn-cyber"
                  onClick={() => setFilter('VULN')}
                  style={{ padding: '4px 12px', fontSize: '0.75rem', background: filter === 'VULN' ? '#F59E0B' : '#14141C', color: filter === 'VULN' ? '#000000' : '#FBBF24' }}
                >
                  CVE Vulnerable
                </button>
                <button
                  className="btn-cyber"
                  onClick={() => setFilter('CROWN')}
                  style={{ padding: '4px 12px', fontSize: '0.75rem', background: filter === 'CROWN' ? '#EC4899' : '#14141C', color: filter === 'CROWN' ? '#FFFFFF' : '#F472B6' }}
                >
                  Crown Jewels
                </button>
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #222230', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '8px' }}>VM Instance</th>
                    <th style={{ padding: '8px' }}>Operating System</th>
                    <th style={{ padding: '8px' }}>IP / Subnet</th>
                    <th style={{ padding: '8px' }}>Hardware</th>
                    <th style={{ padding: '8px' }}>Open Ports</th>
                    <th style={{ padding: '8px' }}>CVEs</th>
                    <th style={{ padding: '8px' }}>Privilege</th>
                  </tr>
                </thead>
                <tbody>
                  {(filter === 'ALL' ? vms : (filter === 'VULN' ? vms.filter(v => v.cves.length > 0) : vms.filter(v => v.is_crown_jewel))).map((v, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #181824' }}>
                      <td style={{ padding: '8px', fontWeight: '600', color: '#FFFFFF' }}>{v.vm_name}</td>
                      <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{v.os}</td>
                      <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', color: '#38BDF8' }}>{v.ip}</td>
                      <td style={{ padding: '8px', fontFamily: 'var(--font-mono)' }}>{v.cpu_cores}c / {v.ram_gb}G</td>
                      <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', color: '#94A3B8' }}>{v.open_ports.join(', ')}</td>
                      <td style={{ padding: '8px' }}>
                        {v.cves.length > 0 ? (
                          <span className="badge badge-amber" style={{ fontSize: '0.68rem' }}>{v.cves[0]}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>None</span>
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
          )}
        </div>
      </div>
    </div>
  );
}
