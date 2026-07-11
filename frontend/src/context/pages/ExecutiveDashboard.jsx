import React, { useEffect, useState } from 'react';
import KPICard from '../components/KPI_Cards/KPICard';
import { getExecutiveKPIs } from '../services/analyticsService';

export default function ExecutiveDashboard() {
  const [kpis, setKpis] = useState(null);

  useEffect(() => {
    getExecutiveKPIs().then(setKpis).catch(console.error);
  }, []);

  return (
    <div>
      <h2>Executive Dashboard</h2>
      <p style={{ color: '#888', marginBottom: '24px' }}>Revenue-at-risk and retention KPI overview.</p>
      {kpis ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {Object.entries(kpis).map(([label, value]) => (
            <KPICard key={label} title={label} value={String(value)} color="#4f46e5" />
          ))}
        </div>
      ) : (
        <p>Loading KPIs... (Run revenue-risk analysis first)</p>
      )}
    </div>
  );
}
