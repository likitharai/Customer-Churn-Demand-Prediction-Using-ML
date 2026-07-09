import React from 'react';
import KPICard from '../components/KPI_Cards/KPICard';

export default function Home() {
  return (
    <div>
      <h1 style={{ marginBottom: '8px' }}>Decision Intelligence Platform</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>AI-powered customer churn prediction and revenue risk analysis.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <KPICard title="Total Customers" value="7,043" subtitle="Telecom dataset" color="#4f46e5" />
        <KPICard title="Churn Rate" value="26.5%" subtitle="Overall churn" color="#e94560" />
        <KPICard title="Best Model Accuracy" value="98.08%" subtitle="KNN + SMOTEENN" color="#10b981" />
        <KPICard title="Revenue at Risk" value="~$2.8M" subtitle="From high-risk customers" color="#f59e0b" />
      </div>
    </div>
  );
}
