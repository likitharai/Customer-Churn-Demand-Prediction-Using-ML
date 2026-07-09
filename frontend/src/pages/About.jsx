import React from 'react';

export default function About() {
  return (
    <div>
      <h2>About</h2>
      <p style={{ color: '#888', marginBottom: '12px' }}>Decision Intelligence Platform — AI-powered churn prediction system.</p>
      <ul style={{ color: '#555', lineHeight: '1.8', paddingLeft: '20px' }}>
        <li>Frontend: React + Vite + Recharts</li>
        <li>Backend: FastAPI + Python</li>
        <li>ML Pipeline: scikit-learn, XGBoost, LightGBM, CatBoost</li>
        <li>Dashboard: Streamlit</li>
        <li>Database: PostgreSQL</li>
        <li>Deployment: Docker + Azure</li>
      </ul>
    </div>
  );
}
