import React from 'react';

interface SidebarProps {
  currentTab: 'queue' | 'detail';
  setCurrentTab: (tab: 'queue' | 'detail') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab }) => {
  return (
    <aside className="sidebar-rail" aria-label="Persistent Navigation">
      {/* 7 Vertical Navigation Dots as specified in Swasthiq UI Mockup */}
      <button
        className="rail-dot"
        title="Clinic Overview"
        aria-label="Clinic Overview"
        onClick={() => setCurrentTab('queue')}
      />

      <button
        className={`rail-dot ${currentTab === 'queue' ? 'active' : ''}`}
        title="1. Handoff Queue"
        aria-label="Handoff Queue"
        onClick={() => setCurrentTab('queue')}
      />

      <button
        className={`rail-dot ${currentTab === 'detail' ? 'active' : ''}`}
        title="2. Conversation Detail"
        aria-label="Conversation Detail"
        onClick={() => setCurrentTab('detail')}
      />

      <button
        className="rail-dot"
        title="Doctor Windows & Schedules"
        aria-label="Doctor Windows & Schedules"
        onClick={() => setCurrentTab('detail')}
      />

      <button
        className="rail-dot"
        title="Patient Directory"
        aria-label="Patient Directory"
        onClick={() => setCurrentTab('queue')}
      />

      <button
        className="rail-dot"
        title="Audit Logs & Determinism"
        aria-label="Audit Logs & Determinism"
        onClick={() => setCurrentTab('detail')}
      />

      <button
        className="rail-dot"
        title="Clinic Configuration"
        aria-label="Clinic Configuration"
        onClick={() => setCurrentTab('queue')}
      />
    </aside>
  );
};
