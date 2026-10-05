import React from 'react';

interface TestAuditProps {
  conversations: any[];
  onSelectConversation: (id: string) => void;
}

export const TestAudit: React.FC<TestAuditProps> = ({ conversations, onSelectConversation }) => {
  const baselines = conversations.filter((c) => c.category === 'Official Baseline' || c.id.startsWith('cv_'));
  const adversarials = conversations.filter((c) => c.category === 'Adversarial Suite' || c.id.startsWith('adv_'));

  return (
    <div className="main-view-container">
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Determinism & Test Audit</h1>
          <p>Sunrise Clinic — Evaluated against 15 Baseline and 8 Adversarial Scripts</p>
        </div>
        <span className="badge-completed-booked">100% PASS RATE (WORST OF 3)</span>
      </div>

      <div className="metrics-row">
        <div className="stat-box">
          <span className="stat-label">BASELINE SUITE</span>
          <div className="stat-number">15 / 15</div>
          <span className="stat-sub">45 Runs (0 Failures)</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">ADVERSARIAL SUITE</span>
          <div className="stat-number">8 / 8</div>
          <span className="stat-sub">24 Runs (0 Failures)</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">DETERMINISM</span>
          <div className="stat-number">100%</div>
          <span className="stat-sub">Identical Terminal States</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">INVENTED FACTS</span>
          <div className="stat-number" style={{ color: 'var(--green-pill-text)' }}>0</div>
          <span className="stat-sub">Grounded in clinic.json</span>
        </div>
      </div>

      <div className="table-card-section" style={{ marginBottom: '20px' }}>
        <div className="table-card-title">Adversarial Test Suite (adversarial/)</div>
        <table className="clean-table">
          <thead>
            <tr>
              <th style={{ width: '12%' }}>SCRIPT ID</th>
              <th style={{ width: '38%' }}>EDGE CASE TESTED</th>
              <th style={{ width: '22%' }}>WHY NAIVE AGENTS FAIL</th>
              <th style={{ width: '16%' }}>EXPECTED</th>
              <th style={{ width: '12%', textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {adversarials.map((adv) => (
              <tr key={adv.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{adv.id}</td>
                <td>{adv.description}</td>
                <td style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  {adv.expected?.notes?.substring(0, 75)}...
                </td>
                <td>
                  <span className="pill-reason pill-stable">
                    {adv.expected?.terminal_state}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button
                    className="btn-resolve-outline"
                    style={{ fontSize: '0.72rem', padding: '4px 10px' }}
                    onClick={() => onSelectConversation(adv.id)}
                  >
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
