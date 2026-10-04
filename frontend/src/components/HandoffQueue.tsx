import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, UserX, HelpCircle, CheckCircle, ExternalLink, Clock } from 'lucide-react';

export interface HandoffItem {
  id: string;
  conversation_id: string;
  caller_said: string;
  all_turns: string[];
  reason: 'clinical_urgent' | 'medical_advice' | 'not_authorised' | 'ambiguous_patient' | 'out_of_scope';
  patient_id?: string | null;
  tool_calls: Array<{ name: string; arguments: Record<string, any> }>;
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
  const [filter, setFilter] = useState<string>('all');

  // Metrics
  const openItems = handoffs.filter((h) => h.status === 'open');
  const clinicalUrgentCount = openItems.filter((h) => h.reason === 'clinical_urgent').length;
  const medicalAdviceCount = openItems.filter((h) => h.reason === 'medical_advice').length;
  const notAuthorisedCount = openItems.filter((h) => h.reason === 'not_authorised').length;
  const ambiguousCount = openItems.filter((h) => h.reason === 'ambiguous_patient').length;

  const filteredHandoffs = handoffs.filter((h) => {
    if (filter === 'all') return h.status === 'open';
    if (filter === 'resolved') return h.status === 'resolved';
    return h.status === 'open' && h.reason === filter;
  });

  const getReasonPill = (reason: string) => {
    switch (reason) {
      case 'clinical_urgent':
        return <span className="pill pill-red"><AlertTriangle size={12} /> clinical_urgent</span>;
      case 'medical_advice':
        return <span className="pill pill-amber"><HelpCircle size={12} /> medical_advice</span>;
      case 'not_authorised':
        return <span className="pill pill-purple"><UserX size={12} /> not_authorised</span>;
      case 'ambiguous_patient':
        return <span className="pill pill-blue"><HelpCircle size={12} /> ambiguous_patient</span>;
      default:
        return <span className="pill pill-gray">{reason}</span>;
    }
  };

  return (
    <div className="content-body">
      {/* Top Counters Ribbon */}
      <div className="metrics-ribbon">
        <div className="metric-card">
          <div className="metric-header">
            <span>Open Escalations</span>
            <ShieldAlert size={16} color="var(--accent-cyan)" />
          </div>
          <div className="metric-value" style={{ color: '#38bdf8' }}>
            {openItems.length}
          </div>
          <span className="metric-desc">Awaiting human triage</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Clinical Urgent</span>
            <AlertTriangle size={16} color="var(--accent-rose)" />
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-rose)' }}>
            {clinicalUrgentCount}
          </div>
          <span className="metric-desc">Immediate clinical priority</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Medical Advice</span>
            <HelpCircle size={16} color="var(--accent-amber)" />
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-amber)' }}>
            {medicalAdviceCount}
          </div>
          <span className="metric-desc">Clinical judgements</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Not Authorised</span>
            <UserX size={16} color="var(--accent-purple)" />
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-purple)' }}>
            {notAuthorisedCount}
          </div>
          <span className="metric-desc">Third-party access refused</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Ambiguous Patient</span>
            <HelpCircle size={16} color="#38bdf8" />
          </div>
          <div className="metric-value" style={{ color: '#38bdf8' }}>
            {ambiguousCount}
          </div>
          <span className="metric-desc">Multiple candidates found</span>
        </div>
      </div>

      {/* Main Queue Card Container */}
      <div className="card-container">
        <div className="card-container-header">
          <div className="card-container-title">
            <Clock size={18} color="var(--accent-cyan)" />
            <span>Escalated Handoff Queue</span>
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['all', 'clinical_urgent', 'not_authorised', 'ambiguous_patient', 'medical_advice', 'resolved'].map(
              (f) => (
                <button
                  key={f}
                  className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '5px 12px' }}
                  onClick={() => setFilter(f)}
                >
                  {f.replace('_', ' ').toUpperCase()}
                </button>
              )
            )}
          </div>
        </div>

        <div className="handoff-list">
          {filteredHandoffs.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No handoffs matching the current filter.
            </div>
          ) : (
            filteredHandoffs.map((item) => (
              <div key={item.id} className="handoff-row">
                <div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      color: '#f8fafc',
                      fontSize: '0.85rem',
                      display: 'block',
                    }}
                  >
                    {item.conversation_id}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>{item.id}</span>
                </div>

                <div>{getReasonPill(item.reason)}</div>

                <div>
                  <div className="caller-utterance-box">
                    "{item.caller_said}"
                  </div>
                  {item.tool_calls.length > 0 && (
                    <div style={{ marginTop: '6px', fontSize: '0.72rem', color: 'var(--text-subtle)' }}>
                      Tools executed before escalation:{' '}
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                        {item.tool_calls.map((t) => t.name).join(', ')}
                      </span>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {item.status === 'open' ? (
                    <button
                      className="btn btn-resolve"
                      onClick={() => onResolve(item.id)}
                    >
                      <CheckCircle size={14} /> Resolve
                    </button>
                  ) : (
                    <span className="pill pill-emerald" style={{ justifyContent: 'center' }}>
                      Resolved
                    </span>
                  )}

                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                    onClick={() => onSelectConversation(item.conversation_id)}
                  >
                    <ExternalLink size={12} /> Transcript
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
