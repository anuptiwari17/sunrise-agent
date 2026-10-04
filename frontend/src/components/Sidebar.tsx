import React from 'react';
import { ShieldAlert, MessageSquareText, Activity, Calendar, Stethoscope, CheckCircle2 } from 'lucide-react';

interface SidebarProps {
  currentTab: 'queue' | 'detail';
  setCurrentTab: (tab: 'queue' | 'detail') => void;
  openHandoffsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  openHandoffsCount,
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-wrapper">
          <div className="brand-icon">
            <Activity size={22} />
          </div>
          <div className="brand-text">
            <h1>Sunrise Clinic</h1>
            <span>Front Desk Agent</span>
          </div>
        </div>
      </div>

      <nav className="nav-section">
        <span className="nav-label">Navigation</span>

        <button
          className={`nav-item ${currentTab === 'queue' ? 'active' : ''}`}
          onClick={() => setCurrentTab('queue')}
        >
          <div className="nav-item-inner">
            <ShieldAlert size={18} />
            <span>Handoff Queue</span>
          </div>
          {openHandoffsCount > 0 && (
            <span className="badge-count">{openHandoffsCount}</span>
          )}
        </button>

        <button
          className={`nav-item ${currentTab === 'detail' ? 'active' : ''}`}
          onClick={() => setCurrentTab('detail')}
        >
          <div className="nav-item-inner">
            <MessageSquareText size={18} />
            <span>Conversation Detail</span>
          </div>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="status-card">
          <div className="status-row">
            <span style={{ color: 'var(--text-subtle)' }}>Engine Status</span>
            <div className="status-indicator">
              <span className="status-dot"></span>
              <span>Online</span>
            </div>
          </div>
          <div className="status-row">
            <span style={{ color: 'var(--text-subtle)' }}>Ref Date</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>2026-10-01</span>
          </div>
          <div className="status-row">
            <span style={{ color: 'var(--text-subtle)' }}>Doctors Active</span>
            <span style={{ color: '#e2e8f0' }}>2 Doctors</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
