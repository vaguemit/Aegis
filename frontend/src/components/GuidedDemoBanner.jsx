import React from 'react';
import {
  Sparkles,
  Play,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  User,
  Server,
  Key,
  Database,
  HelpCircle,
} from 'lucide-react';

export const DEMO_STORIES = [
  {
    id: 'phished_hr_laptop',
    title: 'Story 1: The Phished HR Laptop (Ransomware Attack)',
    subtitle: 'From a single phishing email to full Active Directory domain takeover in 4 steps.',
    startNodeName: 'HR-Workstation-01',
    targetNodeName: 'Primary-Domain-Controller',
    icon: '💻',
    difficulty: 'High Risk',
    narrative: [
      {
        step: 1,
        title: 'Initial Breach (Phishing)',
        actor: 'Alice in HR opens a malicious PDF invoice attachment.',
        action: 'Adversary installs a foothold beacon on HR-Workstation-01.',
        protocol: 'Malicious Payload Execution',
      },
      {
        step: 2,
        title: 'Lateral Pivot via Open Port',
        actor: 'Attacker scans the internal network for weak servers.',
        action: 'Finds Corporate-Web-Portal with unpatched CVE-2020-1472 (ZeroLogon) on Port 445 SMB.',
        protocol: 'SMB / Port 445',
      },
      {
        step: 3,
        title: 'Credential Harvesting',
        actor: 'Attacker dumps memory from the Web Portal.',
        action: 'Extracts cached logon token of SrvAdmin.David (Server Operators group).',
        protocol: 'LSASS Token Steal',
      },
      {
        step: 4,
        title: 'Domain Controller Takeover',
        actor: 'Attacker uses stolen admin privileges.',
        action: 'Logs into Primary-Domain-Controller via DCSync replication and locks the entire enterprise.',
        protocol: 'DCSync / Full Takeover',
      },
    ],
    recommendedFix: 'Apply Security Update KB5034441 to Corporate-Web-Portal to stop the pivot immediately.',
  },
  {
    id: 'rogue_contractor_kerberoast',
    title: 'Story 2: The Rogue Contractor (Kerberoasting Exploit)',
    subtitle: 'A contractor with basic guest permissions steals high-privilege service account tickets.',
    startNodeName: 'Engineering-Workstation-02',
    targetNodeName: 'Customer-SQL-Database',
    icon: '🕵️‍♂️',
    difficulty: 'Critical Risk',
    narrative: [
      {
        step: 1,
        title: 'Low-Privilege Access',
        actor: 'Third-party developer logs in from Engineering-Workstation-02.',
        action: 'Has standard non-admin domain account.',
        protocol: 'Standard Domain Auth',
      },
      {
        step: 2,
        title: 'Kerberoasting SPN Request',
        actor: 'Attacker requests Kerberos TGS service tickets for SPN accounts.',
        action: 'Requests ticket for sql_service account without needing admin rights.',
        protocol: 'Kerberos Port 88 (SPN Request)',
      },
      {
        step: 3,
        title: 'Offline Password Cracking',
        actor: 'Cracks weak NTLM service hash offline with Hashcat.',
        action: 'Recovers plaintext password for Database-Admins group.',
        protocol: 'Offline Hash Cracking',
      },
      {
        step: 4,
        title: 'Customer Data Exfiltration',
        actor: 'Logs in as Database Administrator.',
        action: 'Connects directly to Customer-SQL-Database and exfiltrates 500,000 credit card records.',
        protocol: 'SQL Port 1433 Exfiltration',
      },
    ],
    recommendedFix: 'Enforce 25+ character passwords and AES-256 Kerberos encryption on SPN service accounts.',
  },
  {
    id: 'finance_wire_fraud',
    title: 'Story 3: Finance Wire Fraud (Remote Desktop Pivot)',
    subtitle: 'Attacker compromises finance workstation to pivot to the corporate payment gateway.',
    startNodeName: 'Finance-Workstation-01',
    targetNodeName: 'Payment-Gateway-Host',
    icon: '💳',
    difficulty: 'High Risk',
    narrative: [
      {
        step: 1,
        title: 'Compromised Finance Desktop',
        actor: 'Finance clerk Bob opens infected banking spreadsheet.',
        action: 'Attacker establishes reverse shell on Finance-Workstation-01.',
        protocol: 'Macro Reverse Shell',
      },
      {
        step: 2,
        title: 'RDP Jump to Internal File Share',
        actor: 'Attacker discovers open RDP port on Internal-File-Share.',
        action: 'Pivots across subnet using Bob’s saved Windows credentials.',
        protocol: 'RDP Port 3389',
      },
      {
        step: 3,
        title: 'Payment Gateway Compromise',
        actor: 'Pivots from file share to Payment-Gateway-Host.',
        action: 'Alters outbound wire transfer routing numbers to attacker accounts.',
        protocol: 'HTTPS / API Takeover',
      },
    ],
    recommendedFix: 'Disable Port 3389 RDP across workstations and require dedicated Jump Hosts with MFA.',
  },
];

export default function GuidedDemoBanner({
  currentStoryId,
  onSelectStory,
  onRunStoryPrediction,
  onApplyStoryFix,
}) {
  const currentStory = DEMO_STORIES.find((s) => s.id === currentStoryId) || DEMO_STORIES[0];

  return (
    <div
      style={{
        margin: '0 14px 10px 14px',
        padding: '12px 16px',
        background: 'linear-gradient(90deg, #0D0D14 0%, #151522 100%)',
        border: '1px solid #28283C',
        borderRadius: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      }}
    >
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>{currentStory.icon}</span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '0.92rem', fontWeight: '800', color: '#FFFFFF', margin: 0 }}>
                {currentStory.title}
              </h3>
              <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>{currentStory.difficulty}</span>
            </div>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
              {currentStory.subtitle}
            </p>
          </div>
        </div>

        {/* Story Selector Buttons */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {DEMO_STORIES.map((s) => (
            <button
              key={s.id}
              onClick={() => onSelectStory(s.id)}
              className="btn-cyber"
              style={{
                padding: '5px 10px',
                fontSize: '0.72rem',
                background: currentStoryId === s.id ? '#FFFFFF' : '#14141E',
                color: currentStoryId === s.id ? '#000000' : 'var(--text-secondary)',
                border: currentStoryId === s.id ? '1px solid #FFFFFF' : '1px solid #222230',
              }}
            >
              {s.icon} {s.title.split(':')[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Step-by-Step Story Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${currentStory.narrative.length}, 1fr)`, gap: '8px' }}>
        {currentStory.narrative.map((item) => (
          <div
            key={item.step}
            style={{
              padding: '8px 10px',
              background: '#09090E',
              border: '1px solid #1F1F2C',
              borderRadius: '6px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: '800', color: '#38BDF8' }}>
                  STEP {item.step}
                </span>
                <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>
                  {item.protocol}
                </span>
              </div>
              <div style={{ fontSize: '0.76rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '3px' }}>
                {item.title}
              </div>
              <p style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.3 }}>
                {item.action}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Action Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #1E1E28', paddingTop: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.74rem', color: '#FBBF24' }}>
          <ShieldAlert size={14} color="#FBBF24" />
          <span><strong>Plain-English Fix:</strong> {currentStory.recommendedFix}</span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn-cyber"
            onClick={onRunStoryPrediction}
            style={{
              padding: '6px 14px',
              fontSize: '0.74rem',
              background: '#38BDF8',
              color: '#000000',
              fontWeight: '800',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <Play size={12} fill="#000000" /> 1. Simulate Attack Path
          </button>

          <button
            className="btn-cyber"
            onClick={onApplyStoryFix}
            style={{
              padding: '6px 14px',
              fontSize: '0.74rem',
              background: '#10B981',
              color: '#000000',
              fontWeight: '800',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <ShieldCheck size={14} color="#000000" /> 2. Apply Recommended Fix
          </button>
        </div>
      </div>
    </div>
  );
}
