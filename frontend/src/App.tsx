import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { HandoffQueue, HandoffItem } from './components/HandoffQueue';
import { ConversationDetail } from './components/ConversationDetail';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'queue' | 'detail'>('queue');
  const [handoffs, setHandoffs] = useState<HandoffItem[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string>('cv_0001');

  // Load handoffs
  const loadHandoffs = async () => {
    try {
      const resp = await fetch('/api/handoffs');
      if (resp.ok) {
        const data = await resp.json();
        setHandoffs(data.handoffs || []);
      }
    } catch (err) {
      console.error('Failed to load handoffs:', err);
    }
  };

  // Load conversations
  const loadConversations = async () => {
    try {
      const resp = await fetch('/api/conversations');
      if (resp.ok) {
        const data = await resp.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  useEffect(() => {
    loadHandoffs();
    loadConversations();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      const resp = await fetch(`/api/handoffs/${id}/resolve`, { method: 'POST' });
      if (resp.ok) {
        setHandoffs((prev) =>
          prev.map((h) => (h.id === id ? { ...h, status: 'resolved' } : h))
        );
      }
    } catch (err) {
      console.error('Failed to resolve handoff:', err);
    }
  };

  const handleSelectConversation = (convId: string) => {
    setSelectedConvId(convId);
    setCurrentTab('detail');
  };

  const openHandoffsCount = handoffs.filter((h) => h.status === 'open').length;

  return (
    <div className="app-container">
      {/* Shared Sidebar Persistent Across Both Screens */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        openHandoffsCount={openHandoffsCount}
      />

      {/* Main Workspace Area */}
      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-title">
            <h2>
              {currentTab === 'queue'
                ? 'Clinical Handoff & Escalation Queue'
                : 'Conversation Trace & Grounding Inspector'}
            </h2>
            <div className="top-bar-subtitle">
              {currentTab === 'queue'
                ? 'Deterministic triage of conversations exceeding front-desk remit'
                : 'Visual proof of grounding with inline tool execution chips'}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                color: '#34d399',
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
              }}
            >
              Zero Invented Facts Enforced
            </span>
          </div>
        </header>

        {currentTab === 'queue' ? (
          <HandoffQueue
            handoffs={handoffs}
            onResolve={handleResolve}
            onSelectConversation={handleSelectConversation}
          />
        ) : (
          <ConversationDetail
            conversations={conversations}
            selectedConvId={selectedConvId}
            onSelectConvId={setSelectedConvId}
          />
        )}
      </main>
    </div>
  );
};

export default App;
