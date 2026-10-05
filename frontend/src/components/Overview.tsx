import React from 'react';

interface OverviewProps {
  clinicData: any;
  onNavigate: (tab: any) => void;
  openHandoffsCount: number;
}

export const Overview: React.FC<OverviewProps> = ({ clinicData, onNavigate, openHandoffsCount }) => {
  return (
    <div className="main-view-container">
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Clinic Overview</h1>
          <p>Sunrise Clinic, Dehradun — System Status & Operational Metrics</p>
        </div>
        <span className="badge-completed-booked">SYSTEM HEALTHY</span>
      </div>

      {/* Metric Cards Ribbon */}
      <div className="metrics-row">
        <div className="stat-box">
          <span className="stat-label">DATE ANCHOR</span>
          <div className="stat-number" style={{ fontSize: '1.4rem' }}>
            {clinicData?.clinic?.reference_date || '2026-10-01'}
          </div>
          <span className="stat-sub">Strict Request Anchor</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">ACTIVE DOCTORS</span>
          <div className="stat-number">{clinicData?.doctors?.length || 2}</div>
          <span className="stat-sub">Dr. Rao & Dr. Sethi</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">REGISTERED PATIENTS</span>
          <div className="stat-number">{clinicData?.patients?.length || 40}</div>
          <span className="stat-sub">clinic.json Ground Truth</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">OPEN ESCALATIONS</span>
          <div className="stat-number">{openHandoffsCount}</div>
          <span className="stat-sub urgent-red">Requires Human Review</span>
        </div>
      </div>

      {/* Two Column Feature Cards */}
      <div className="conv-detail-grid">
        <div className="table-card-section">
          <div className="table-card-title">Clinic Front Desk Automation Remit</div>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '14px' }}>
            The AI Front Desk Agent is strictly authorized to execute 6 ground-truth tools against <strong>clinic.json</strong>.
            Double-booking prevention is enforced via atomic locks, with zero invented slots or facts.
          </p>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button className="btn-resolve-solid" onClick={() => onNavigate('queue')}>
              Open Handoff Queue (Screen 1)
            </button>
            <button className="btn-resolve-outline" onClick={() => onNavigate('detail')}>
              Open Conversation Detail (Screen 2)
            </button>
          </div>
        </div>

        <div className="table-card-section">
          <div className="table-card-title">The One Hard Safety Rule</div>
          <p style={{ fontSize: '0.84rem', color: '#b91c1c', lineHeight: '1.6', marginBottom: '12px' }}>
            Any caller describing acute clinical distress (chest pain, stroke, breathlessness, profuse bleeding) is halted immediately.
            The agent cancels any ongoing booking flow and hands off to clinic staff.
          </p>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-resolve-outline" onClick={() => onNavigate('doctors')}>
              View Doctor Schedules
            </button>
            <button className="btn-resolve-outline" onClick={() => onNavigate('patients')}>
              Search Patient Directory
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
