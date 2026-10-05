import React, { useState, useEffect } from 'react';
import { Sidebar, TabKey } from './components/Sidebar';
import { HandoffQueue, HandoffItem } from './components/HandoffQueue';
import { ConversationDetail } from './components/ConversationDetail';
import { Overview } from './components/Overview';
import { DoctorSchedules } from './components/DoctorSchedules';
import { PatientDirectory } from './components/PatientDirectory';
import { TestAudit } from './components/TestAudit';
import { SettingsView } from './components/SettingsView';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<TabKey>('queue');
  const [handoffs, setHandoffs] = useState<HandoffItem[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [clinicData, setClinicData] = useState<any>(null);
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

  // Load clinic data (doctors, patients, holidays) from backend
  const loadClinicData = async () => {
    try {
      const resp = await fetch('/api/clinic-info');
      if (resp.ok) {
        const data = await resp.json();
        setClinicData(data);
      }
    } catch (err) {
      console.error('Failed to load clinic data:', err);
    }
  };

  useEffect(() => {
    loadHandoffs();
    loadConversations();
    loadClinicData();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await fetch(`/api/handoffs/${id}/resolve`, { method: 'POST' });
    } catch (err) {
      console.error('Failed to resolve handoff:', err);
    }
    setHandoffs((prev) =>
      prev.map((h) => (h.id === id ? { ...h, status: 'resolved' } : h))
    );
  };

  const handleSelectConversation = (convId: string) => {
    setSelectedConvId(convId);
    setCurrentTab('detail');
  };

  const getSuperHeaderTitle = () => {
    switch (currentTab) {
      case 'overview':
        return 'Sunrise Clinic — Overview';
      case 'queue':
        return '1. Handoff Queue';
      case 'detail':
        return '2. Conversation Detail';
      case 'doctors':
        return 'Doctor Schedules & Shift Windows';
      case 'patients':
        return 'Patient Directory & Verification';
      case 'audit':
        return 'Determinism & Test Audit';
      case 'settings':
        return 'Engine & LLM Configuration';
      default:
        return 'Sunrise Clinic';
    }
  };

  const openHandoffsCount = handoffs.filter((h) => h.status === 'open').length;

  return (
    <div>
      {/* Super Header matching Swasthiq assignment screenshot styling */}
      <div className="page-super-header">{getSuperHeaderTitle()}</div>

      {/* Main Persistent Card Wrapper */}
      <div className="app-card-wrapper">
        {/* Shared Persistent Sidebar Rail with all 7 fully functional dots */}
        <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />

        {/* View Switcher */}
        {currentTab === 'overview' && (
          <Overview
            clinicData={clinicData}
            onNavigate={setCurrentTab}
            openHandoffsCount={openHandoffsCount}
          />
        )}

        {currentTab === 'queue' && (
          <HandoffQueue
            handoffs={handoffs}
            onResolve={handleResolve}
            onSelectConversation={handleSelectConversation}
          />
        )}

        {currentTab === 'detail' && (
          <ConversationDetail
            conversations={conversations}
            selectedConvId={selectedConvId}
            onSelectConvId={setSelectedConvId}
          />
        )}

        {currentTab === 'doctors' && (
          <DoctorSchedules clinicData={clinicData} />
        )}

        {currentTab === 'patients' && (
          <PatientDirectory clinicData={clinicData} />
        )}

        {currentTab === 'audit' && (
          <TestAudit
            conversations={conversations}
            onSelectConversation={handleSelectConversation}
          />
        )}

        {currentTab === 'settings' && <SettingsView />}
      </div>
    </div>
  );
};

export default App;
