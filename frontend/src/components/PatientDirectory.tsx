import React, { useState } from 'react';

interface PatientDirectoryProps {
  clinicData: any;
}

export const PatientDirectory: React.FC<PatientDirectoryProps> = ({ clinicData }) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const patients = clinicData?.patients || [];

  const filteredPatients = patients.filter((p: any) => {
    const q = searchTerm.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.phone?.includes(q) ||
      p.id?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="main-view-container">
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Patient Directory & Disambiguation</h1>
          <p>Sunrise Clinic, Dehradun — 40 Registered Patients in clinic.json</p>
        </div>
        <span className="badge-open">{filteredPatients.length} MATCHES</span>
      </div>

      <div className="script-selector-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            Search Directory:
          </span>
          <input
            type="text"
            className="script-select-dropdown"
            style={{ width: '320px', padding: '6px 12px' }}
            placeholder="Type 'Sharma', 'Priya', or mobile number..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button
            className="btn-resolve-outline"
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            onClick={() => setSearchTerm('Sharma')}
          >
            Demo Ambiguity ("Sharma")
          </button>
          <button
            className="btn-resolve-outline"
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            onClick={() => setSearchTerm('')}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="table-card-section">
        <div className="table-card-title">
          {searchTerm.toLowerCase() === 'sharma' ? (
            <span style={{ color: 'var(--yellow-pill-text)' }}>
              Ambiguity Demonstration: 3 Patients Match "Sharma" → Agent Escalates with <code>ambiguous_patient</code>
            </span>
          ) : (
            'Registered Patient Records'
          )}
        </div>

        <table className="clean-table">
          <thead>
            <tr>
              <th style={{ width: '15%' }}>PATIENT ID</th>
              <th style={{ width: '30%' }}>FULL NAME</th>
              <th style={{ width: '25%' }}>PHONE NUMBER</th>
              <th style={{ width: '30%' }}>GUARDIAN INFO</th>
            </tr>
          </thead>
          <tbody>
            {filteredPatients.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-subtle)' }}>
                  No matching patients found.
                </td>
              </tr>
            ) : (
              filteredPatients.slice(0, 15).map((p: any) => (
                <tr key={p.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--blue-pill-text)' }}>
                    {p.id}
                  </td>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.phone}</td>
                  <td>
                    {p.guardian_of ? (
                      <span className="pill-reason pill-stable">Guardian of {p.guardian_of}</span>
                    ) : p.guardian_id ? (
                      <span className="pill-reason pill-not-auth">Minor (Guardian: {p.guardian_id})</span>
                    ) : (
                      <span style={{ color: 'var(--text-subtle)', fontSize: '0.75rem' }}>Self</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
