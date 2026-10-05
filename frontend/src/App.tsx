import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { HandoffQueue, HandoffItem } from './components/HandoffQueue';
import { ConversationDetail } from './components/ConversationDetail';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'queue' | 'detail'>('queue');
  const [handoffs, setHandoffs] = useState<HandoffItem[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string>('cv_4471');

  // Load handoffs from backend
  const loadHandoffs = async () => {
    try {
      const resp = await fetch('/api/handoffs');
      if (resp.ok) {
        const data = await resp.json();
        if (data.handoffs && data.handoffs.length > 0) {
          setHandoffs(data.handoffs);
        }
      }
    } catch (err) {
      console.error('Failed to load handoffs:', err);
    }
  };

  // Load conversation test scripts from backend
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
      await fetch(`/api/handoffs/${id}/resolve`, { method: 'POST' });
    } catch (err) {
      console.error('Failed to resolve handoff:', err);
    }
    // Optimistically update UI
    setHandoffs((prev) =>
      prev.map((h) => (h.id === id ? { ...h, status: 'resolved' } : h))
    );
  };

  const handleSelectConversation = (convId: string) => {
    setSelectedConvId(convId);
    setCurrentTab('detail');
  };

  return (
    <div>
      {/* Super Header Number matching Assignment Mockups (e.g. "1. Handoff Queue" / "2. Conversation Detail") */}
      <div className="page-super-header">
        {currentTab === 'queue' ? '1. Handoff Queue' : '2. Conversation Detail'}
      </div>

      {/* Main Persistent Card Wrapper */}
      <div className="app-card-wrapper">
        {/* Shared Persistent Sidebar Rail with 7 circular dots */}
        <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />

        {/* View Switcher */}
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
      </div>
    </div>
  );
};

export default App;
