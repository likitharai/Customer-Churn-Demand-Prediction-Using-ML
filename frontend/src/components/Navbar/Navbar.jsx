import React from 'react';

export default function Navbar() {
  return (
    <nav style={{ background: '#1a1a2e', color: '#fff', padding: '0 24px', height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span style={{ fontWeight: 700, fontSize: '1.2rem' }}>🧠 Decision Intelligence Platform</span>
      <span style={{ fontSize: '0.85rem', opacity: 0.7 }}>Customer Churn & Revenue Risk</span>
    </nav>
  );
}
