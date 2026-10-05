import React from 'react';

export type TabKey = 'overview' | 'queue' | 'detail' | 'doctors' | 'patients' | 'audit' | 'settings';

interface SidebarProps {
  currentTab: TabKey;
  setCurrentTab: (tab: TabKey) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab }) => {
  return (
    <aside className="sidebar-rail" aria-label="Persistent Navigation Rail">
      {/* Dot 1: Clinic Overview */}
      <button
        className={`rail-dot ${currentTab === 'overview' ? 'active' : ''}`}
        title="1. Clinic Overview"
        aria-label="Clinic Overview"
        onClick={() => setCurrentTab('overview')}
      />

      {/* Dot 2: Screen 1 - Handoff Queue */}
      <button
        className={`rail-dot ${currentTab === 'queue' ? 'active' : ''}`}
        title="2. Handoff Queue (Screen 1)"
        aria-label="Handoff Queue"
        onClick={() => setCurrentTab('queue')}
      />

      {/* Dot 3: Screen 2 - Conversation Detail */}
      <button
        className={`rail-dot ${currentTab === 'detail' ? 'active' : ''}`}
        title="3. Conversation Detail (Screen 2)"
        aria-label="Conversation Detail"
        onClick={() => setCurrentTab('detail')}
      />

      {/* Dot 4: Doctor Schedules & Windows */}
      <button
        className={`rail-dot ${currentTab === 'doctors' ? 'active' : ''}`}
        title="4. Doctor Schedules & Windows"
        aria-label="Doctor Schedules & Windows"
        onClick={() => setCurrentTab('doctors')}
      />

      {/* Dot 5: Patient Directory & Disambiguation */}
      <button
        className={`rail-dot ${currentTab === 'patients' ? 'active' : ''}`}
        title="5. Patient Directory (40 Patients)"
        aria-label="Patient Directory"
        onClick={() => setCurrentTab('patients')}
      />

      {/* Dot 6: Determinism & Test Audit */}
      <button
        className={`rail-dot ${currentTab === 'audit' ? 'active' : ''}`}
        title="6. Determinism & Test Audit"
        aria-label="Determinism & Test Audit"
        onClick={() => setCurrentTab('audit')}
      />

      {/* Dot 7: Engine & LLM Configuration */}
      <button
        className={`rail-dot ${currentTab === 'settings' ? 'active' : ''}`}
        title="7. Engine & LLM Settings"
        aria-label="Engine & LLM Settings"
        onClick={() => setCurrentTab('settings')}
      />
    </aside>
  );
};
