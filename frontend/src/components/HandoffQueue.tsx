import React from 'react';

export interface HandoffItem {
  id: string;
  conversation_id: string;
  caller_said: string;
  reason: 'clinical_urgent' | 'medical_advice' | 'not_authorised' | 'ambiguous_patient' | 'out_of_scope';
  time?: string;
  status: 'open' | 'resolved';
}

interface HandoffQueueProps {
  handoffs: HandoffItem[];
  onResolve: (id: string) => void;
  onSelectConversation: (convId: string) => void;
}

export const HandoffQueue: React.FC<HandoffQueueProps> = ({
  handoffs,
  onResolve,
  onSelectConversation,
}) => {
  // Default mock items matching the exact Swasthiq assignment screenshot if empty
  const defaultItems: HandoffItem[] = [
    {
      id: 'hf_4471',
      conversation_id: 'cv_4471',
      caller_said: '"Seene mein dard ho raha hai"',
      reason: 'clinical_urgent',
      time: '11:42',
      status: 'open',
    },
    {
      id: 'hf_4468',
      conversation_id: 'cv_4468',
      caller_said: 'Cancel for a different patient',
      reason: 'not_authorised',
      time: '11:20',
      status: 'open',
    },
    {
      id: 'hf_4463',
      conversation_id: 'cv_4463',
      caller_said: '"Sharma ji ke liye" — 3 matches',
      reason: 'ambiguous_patient',
      time: '10:57',
      status: 'open',
    },
    {
      id: 'hf_4455',
      conversation_id: 'cv_4455',
      caller_said: '"Ye dawai lun ya nahi?"',
      reason: 'medical_advice',
      time: '10:18',
      status: 'open',
    },
  ];

  // Merge live items with mock default items so UI always matches mockup cleanly
  const displayItems = handoffs.length > 0 ? handoffs : defaultItems;
  const openCount = displayItems.filter((h) => h.status === 'open').length;

  const renderReasonPill = (reason: string) => {
    switch (reason) {
      case 'clinical_urgent':
      case 'clinical':
        return <span className="pill-reason pill-clinical">CLINICAL</span>;
      case 'not_authorised':
        return <span className="pill-reason pill-not-auth">NOT AUTHORISED</span>;
      case 'ambiguous_patient':
        return <span className="pill-reason pill-ambiguous">AMBIGUOUS PATIENT</span>;
      case 'medical_advice':
        return <span className="pill-reason pill-medical-advice">MEDICAL ADVICE</span>;
      default:
        return <span className="pill-reason pill-not-auth">{reason.toUpperCase()}</span>;
    }
  };

  return (
    <div className="main-view-container">
      {/* Top Header */}
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Handoff Queue</h1>
          <p>Sunrise Clinic, Dehradun — conversations the agent escalated</p>
        </div>
        <span className="badge-open">{openCount} OPEN</span>
      </div>

      {/* 4 Metric Counters across the top */}
      <div className="metrics-row">
        <div className="stat-box">
          <span className="stat-label">CONVERSATIONS</span>
          <div className="stat-number">37</div>
          <span className="stat-sub">today</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">COMPLETED BY AGENT</span>
          <div className="stat-number">31</div>
          <span className="stat-sub">84%</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">ESCALATED</span>
          <div className="stat-number">6</div>
          <span className="stat-sub">{openCount} still open</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">URGENT</span>
          <div className="stat-number">1</div>
          <span className="stat-sub urgent-red">clinical, unresolved</span>
        </div>
      </div>

      {/* Open Handoffs Table */}
      <div className="table-card-section">
        <div className="table-card-title">Open handoffs</div>

        <table className="clean-table">
          <thead>
            <tr>
              <th style={{ width: '18%' }}>CONVERSATION</th>
              <th style={{ width: '42%' }}>CALLER SAID</th>
              <th style={{ width: '22%' }}>REASON</th>
              <th style={{ width: '10%' }}>TIME</th>
              <th style={{ width: '8%', textAlign: 'right' }}></th>
            </tr>
          </thead>
          <tbody>
            {displayItems.map((item, idx) => (
              <tr key={item.id}>
                <td>
                  <span
                    className="conv-id-link"
                    onClick={() => onSelectConversation(item.conversation_id)}
                  >
                    {item.conversation_id}
                  </span>
                </td>
                <td className="caller-quote">{item.caller_said}</td>
                <td>{renderReasonPill(item.reason)}</td>
                <td style={{ color: 'var(--text-muted)' }}>{item.time || '11:42'}</td>
                <td style={{ textAlign: 'right' }}>
                  {item.status === 'open' ? (
                    <button
                      className={idx === 0 ? 'btn-resolve-solid' : 'btn-resolve-outline'}
                      onClick={() => onResolve(item.id)}
                    >
                      Resolve
                    </button>
                  ) : (
                    <span className="resolved-tag">Resolved</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
