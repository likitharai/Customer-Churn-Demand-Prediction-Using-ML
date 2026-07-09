import React from 'react';

export default function KPICard({ title, value, subtitle, color = '#e94560' }) {
  return (
    <div style={{ background: '#fff', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 12px rgba(0,0,0,0.08)', borderTop: `4px solid ${color}` }}>
      <p style={{ fontSize: '0.8rem', color: '#888', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</p>
      <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#1a1a2e' }}>{value}</p>
      {subtitle && <p style={{ fontSize: '0.78rem', color: '#aaa', marginTop: '6px' }}>{subtitle}</p>}
    </div>
  );
}
