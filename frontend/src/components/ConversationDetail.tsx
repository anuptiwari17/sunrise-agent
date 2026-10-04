import React, { useState, useEffect } from 'react';
import { Play, Copy, Check, Terminal, FileCode2, User, Bot, Sparkles, ChevronDown, ChevronRight, Layers } from 'lucide-react';

interface ToolCall {
  name: string;
  arguments: Record<string, any>;
}

interface RunMetrics {
  turns: number;
  tokens: number;
  latency_ms: number;
}

interface ConversationResult {
  conversation_id: string;
  tool_calls: ToolCall[];
  terminal_state: string;
  escalation_reason: string | null;
  patient_id: string | null;
  appointment_id: string | null;
  reply: string;
  metrics: RunMetrics;
}

interface ConversationItem {
  id: string;
  category: string;
  description: string;
  today: string;
  turns: string[];
  expected: any;
}

interface ConversationDetailProps {
  conversations: ConversationItem[];
  selectedConvId: string;
  onSelectConvId: (id: string) => void;
}

export const ConversationDetail: React.FC<ConversationDetailProps> = ({
  conversations,
  selectedConvId,
  onSelectConvId,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ConversationResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});

  const currentScript = conversations.find((c) => c.id === selectedConvId) || conversations[0];

  const runConversation = async (convId: string) => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/conversations/${convId}/run`);
      if (resp.ok) {
        const data = await resp.json();
        setResult(data.result);
      }
    } catch (err) {
      console.error('Failed to run conversation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedConvId) {
      runConversation(selectedConvId);
    }
  }, [selectedConvId]);

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleToolExpand = (index: number) => {
    setExpandedTools((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const getTerminalBadge = (state: string) => {
    switch (state) {
      case 'booked':
        return <span className="pill pill-emerald">booked</span>;
      case 'rescheduled':
        return <span className="pill pill-blue">rescheduled</span>;
      case 'cancelled':
        return <span className="pill pill-amber">cancelled</span>;
      case 'escalated':
        return <span className="pill pill-red">escalated</span>;
      case 'refused':
        return <span className="pill pill-purple">refused</span>;
      case 'abandoned':
        return <span className="pill pill-gray">abandoned</span>;
      default:
        return <span className="pill pill-gray">{state}</span>;
    }
  };

  return (
    <div className="content-body">
      {/* Top Selector & Execution Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-xl)',
          padding: '16px 24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 600 }}>
              SELECT CONVERSATION SCRIPT
            </span>
            <select
              value={selectedConvId}
              onChange={(e) => onSelectConvId(e.target.value)}
              style={{
                background: '#1e293b',
                color: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 14px',
                fontSize: '0.88rem',
                fontWeight: 600,
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              <optgroup label="Official Baseline Scripts (conversations/)">
                {conversations
                  .filter((c) => c.category === 'Official Baseline')
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} — {c.description.substring(0, 45)}...
                    </option>
                  ))}
              </optgroup>
              <optgroup label="Adversarial Test Suite (adversarial/)">
                {conversations
                  .filter((c) => c.category === 'Adversarial Suite')
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} — {c.description.substring(0, 45)}...
                    </option>
                  ))}
              </optgroup>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 600 }}>
              TODAY ANCHOR
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                background: 'rgba(2, 132, 199, 0.1)',
                color: '#38bdf8',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.82rem',
                border: '1px solid rgba(2, 132, 199, 0.25)',
              }}
            >
              {currentScript?.today || '2026-10-01'}
            </span>
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => runConversation(selectedConvId)}
          disabled={loading}
        >
          <Play size={16} /> {loading ? 'Running Agent...' : 'Live Run via /agent/run'}
        </button>
      </div>

      {/* Script Description Note */}
      {currentScript && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-color)',
            borderLeft: '4px solid var(--accent-cyan)',
            padding: '14px 20px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            color: '#cbd5e1',
          }}
        >
          <strong>Scenario:</strong> {currentScript.description}{' '}
          {currentScript.expected?.notes && (
            <span style={{ color: 'var(--text-subtle)', display: 'block', marginTop: '4px' }}>
              <strong>Expected Note:</strong> {currentScript.expected.notes}
            </span>
          )}
        </div>
      )}

      {/* Main Split: Transcript with Inline Tool Calls on Left, Outcome Panel on Right */}
      <div className="conversation-split">
        {/* Left Column: Interactive Multi-turn Transcript with Inline Tools */}
        <div className="card-container">
          <div className="card-container-header">
            <div className="card-container-title">
              <Terminal size={18} color="var(--accent-cyan)" />
              <span>Multi-Turn Grounded Transcript</span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
              Tools rendered inline at exact execution point
            </span>
          </div>

          <div className="chat-thread">
            {currentScript?.turns.map((turn, idx) => (
              <React.Fragment key={idx}>
                {/* Caller Utterance */}
                <div className="chat-bubble-container">
                  <div className="chat-bubble-caller">
                    <div className="bubble-meta">
                      <User size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      Caller Turn #{idx + 1}
                    </div>
                    {turn}
                  </div>
                </div>

                {/* Inline Tool Call(s) associated with this step */}
                {result?.tool_calls &&
                  idx === currentScript.turns.length - 1 &&
                  result.tool_calls.map((tool, tIdx) => (
                    <div key={tIdx} className="inline-tool-chip">
                      <div
                        className="tool-chip-header"
                        style={{ cursor: 'pointer' }}
                        onClick={() => toggleToolExpand(tIdx)}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Sparkles size={14} color="#38bdf8" />
                          <span>TOOL CALL: {tool.name}()</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span className="tool-chip-badge">Grounded In clinic.json</span>
                          {expandedTools[tIdx] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </div>
                      </div>

                      <div className="tool-chip-code">
                        <pre style={{ margin: 0 }}>
                          {tool.name}({JSON.stringify(tool.arguments, null, 2)})
                        </pre>
                      </div>
                    </div>
                  ))}
              </React.Fragment>
            ))}

            {/* Agent's Final Reply */}
            {result && (
              <div className="chat-bubble-container" style={{ alignSelf: 'flex-end', width: '100%' }}>
                <div className="chat-bubble-agent">
                  <div className="bubble-meta" style={{ color: '#bae6fd' }}>
                    <Bot size={12} style={{ display: 'inline', marginRight: '4px' }} />
                    Sunrise Clinic Receptionist
                  </div>
                  {result.reply}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Machine-Readable Outcome Panel */}
        <div className="outcome-panel">
          <div className="inspector-card">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
                <Layers size={18} color="var(--accent-cyan)" />
                <span>Outcome Inspector</span>
              </div>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.72rem', padding: '4px 8px' }}
                onClick={copyToClipboard}
              >
                {copied ? <Check size={12} color="var(--accent-emerald)" /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>

            {result ? (
              <>
                <div className="inspector-field">
                  <span className="inspector-label">Terminal State</span>
                  <div>{getTerminalBadge(result.terminal_state)}</div>
                </div>

                <div className="inspector-field">
                  <span className="inspector-label">Escalation Reason</span>
                  <div className="inspector-value">
                    {result.escalation_reason ? (
                      <span className="pill pill-red">{result.escalation_reason}</span>
                    ) : (
                      <span style={{ color: 'var(--text-subtle)' }}>null (Not Escalated)</span>
                    )}
                  </div>
                </div>

                <div className="inspector-field">
                  <span className="inspector-label">Patient ID</span>
                  <div className="inspector-value" style={{ color: result.patient_id ? '#38bdf8' : 'var(--text-subtle)' }}>
                    {result.patient_id || 'null'}
                  </div>
                </div>

                <div className="inspector-field">
                  <span className="inspector-label">Appointment ID</span>
                  <div className="inspector-value" style={{ color: result.appointment_id ? '#34d399' : 'var(--text-subtle)' }}>
                    {result.appointment_id || 'null'}
                  </div>
                </div>

                <div
                  style={{
                    borderTop: '1px solid var(--border-color)',
                    paddingTop: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <span className="inspector-label">Execution Metrics</span>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Latency:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                      {result.metrics?.latency_ms ?? 0} ms
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Total Turns:</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{result.metrics?.turns ?? 0}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Estimated Tokens:</span>
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{result.metrics?.tokens ?? 0}</span>
                  </div>
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px' }}>
                Loading conversation result...
              </div>
            )}
          </div>

          {/* Raw Contract JSON Viewer */}
          {result && (
            <div className="inspector-card" style={{ padding: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <FileCode2 size={14} color="var(--text-subtle)" />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 600 }}>
                  SCHEMA.MD JSON OUTPUT
                </span>
              </div>
              <pre
                style={{
                  margin: 0,
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  color: '#94a3b8',
                  background: 'rgba(0, 0, 0, 0.4)',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  maxHeight: '180px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
