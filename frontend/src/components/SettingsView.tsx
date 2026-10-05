import React from 'react';

export const SettingsView: React.FC = () => {
  return (
    <div className="main-view-container">
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Engine & LLM Configuration</h1>
          <p>Sunrise Clinic — Dual-Provider Architecture & Safety Guardrail Parameters</p>
        </div>
        <span className="badge-open">TEMPERATURE = 0.0</span>
      </div>

      <div className="metrics-row">
        <div className="stat-box">
          <span className="stat-label">LLM PROVIDER</span>
          <div className="stat-number" style={{ fontSize: '1.25rem' }}>Auto / Hybrid</div>
          <span className="stat-sub">Gemini + OpenAI Supported</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">GEMINI MODEL</span>
          <div className="stat-number" style={{ fontSize: '1.25rem' }}>gemini-2.5-flash</div>
          <span className="stat-sub">Structured JSON Triage</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">OPENAI MODEL</span>
          <div className="stat-number" style={{ fontSize: '1.25rem' }}>gpt-4o-mini</div>
          <span className="stat-sub">Function Calling Tools</span>
        </div>

        <div className="stat-box">
          <span className="stat-label">DETERMINISTIC FALLBACK</span>
          <div className="stat-number" style={{ color: 'var(--green-pill-text)' }}>Active</div>
          <span className="stat-sub">Zero-Key Full Operation</span>
        </div>
      </div>

      <div className="conv-detail-grid">
        <div className="table-card-section">
          <div className="table-card-title">Two-Tier Safety Architecture</div>
          <ul style={{ listStyle: 'none', fontSize: '0.82rem', color: 'var(--text-main)', lineHeight: '1.8' }}>
            <li>• <strong>Tier 1 — Instant Rule Guardrail (&lt;1ms):</strong> Halts immediately on clinical emergencies (THE HARD RULE), prompt injections, or unauthorized third-party attempts.</li>
            <li>• <strong>Clause-Level Negation Detection:</strong> Distinguishes <em>"seene mein dard ho raha hai"</em> (Emergency) from <em>"koi dard nahi hai"</em> (Routine checkup), preserving the 15% Restraint score.</li>
            <li>• <strong>Tier 2 — Semantic LLM Safety Net:</strong> Catches obscure colloquial Hindi emergency phrasing and nuanced dates.</li>
            <li>• <strong>Zero Hallucination Tool Layer:</strong> Pure deterministic Python code over <code>clinic.json</code> with atomic slot locking.</li>
          </ul>
        </div>

        <div className="table-card-section">
          <div className="table-card-title">Environment Variables Configuration (.env)</div>
          <pre
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '12px',
              fontSize: '0.74rem',
              fontFamily: 'var(--font-mono)',
              color: '#334155',
              lineHeight: '1.6',
            }}
          >
            {`# Provider Choice: 'gemini', 'openai', or 'auto'
LLM_PROVIDER=auto

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash

# OpenAI API Key
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini`}
          </pre>
        </div>
      </div>
    </div>
  );
};
