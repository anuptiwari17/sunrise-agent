import React from 'react';

interface DoctorSchedulesProps {
  clinicData: any;
}

export const DoctorSchedules: React.FC<DoctorSchedulesProps> = ({ clinicData }) => {
  const doctors = clinicData?.doctors || [
    {
      id: 'dr_rao',
      name: 'Dr. Anjali Rao',
      specialty: 'General Physician',
      consultation_fee: 500,
      shift_windows: [
        { day: 'Monday', window: '09:00 - 12:00, 11:45 - 15:00 (Union Deduplicated)' },
        { day: 'Wednesday', window: '09:00 - 13:00' },
        { day: 'Friday', window: '09:00 - 13:00, 16:00 - 19:00' },
        { day: 'Saturday', window: '10:00 - 14:00' },
      ],
    },
    {
      id: 'dr_sethi',
      name: 'Dr. Rajiv Sethi',
      specialty: 'Paediatrics',
      consultation_fee: 600,
      shift_windows: [
        { day: 'Tuesday', window: '10:00 - 14:00, 17:00 - 20:00' },
        { day: 'Thursday', window: '10:00 - 14:00, 17:00 - 20:00' },
        { day: 'Saturday', window: '09:00 - 13:00' },
      ],
    },
  ];

  const holidays = clinicData?.holidays || ['2026-10-02 (Gandhi Jayanti)'];

  return (
    <div className="main-view-container">
      <div className="screen-header">
        <div className="screen-header-left">
          <h1>Doctor Schedules & Shift Windows</h1>
          <p>Sunrise Clinic, Dehradun — Ground Truth Rosters in clinic.json</p>
        </div>
        <span className="badge-open">15-MIN INTERVAL SLOTS</span>
      </div>

      <div className="metrics-row">
        {doctors.map((doc: any) => (
          <div key={doc.id} className="stat-box" style={{ gridColumn: 'span 2' }}>
            <span className="stat-label">{(doc.specialty || doc.specialization || 'DOCTOR').toUpperCase()}</span>
            <div className="stat-number" style={{ fontSize: '1.25rem' }}>{doc.name}</div>
            <span className="stat-sub">Fee: ₹{doc.consultation_fee || 500} per 15-min consultation</span>

            <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Shift Windows:
              </div>
              <ul style={{ listStyle: 'none', fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
                {doc.id === 'dr_rao' ? (
                  <>
                    <li>• <strong>Monday:</strong> 09:00–12:00 & 11:45–15:00 <em>(union deduplicated)</em></li>
                    <li>• <strong>Wednesday:</strong> 09:00–13:00</li>
                    <li>• <strong>Friday:</strong> 09:00–13:00 & 16:00–19:00</li>
                    <li>• <strong>Saturday:</strong> 10:00–14:00</li>
                  </>
                ) : (
                  <>
                    <li>• <strong>Tuesday:</strong> 10:00–14:00 & 17:00–20:00</li>
                    <li>• <strong>Thursday:</strong> 10:00–14:00 & 17:00–20:00</li>
                    <li>• <strong>Saturday:</strong> 09:00–13:00</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="table-card-section">
        <div className="table-card-title">Clinic Holiday Calendar</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
          On clinic holidays, no appointments can be scheduled. The tool <code>search_slots</code> returns an empty list, and the agent politely explains the clinic is closed.
        </p>
        <div style={{ display: 'flex', gap: '8px' }}>
          {holidays.map((h: string, idx: number) => (
            <span key={idx} className="pill-reason pill-clinical" style={{ fontSize: '0.75rem' }}>
              {h}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
