import React from 'react';
import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: '🏠 Home' },
  { to: '/executive', label: '📊 Executive Dashboard' },
  { to: '/customers', label: '👥 Customer Analytics' },
  { to: '/prediction', label: '🤖 Prediction' },
  { to: '/revenue', label: '💰 Revenue Risk' },
  { to: '/recommendations', label: '💡 Recommendations' },
  { to: '/shap', label: '🔍 SHAP Analysis' },
  { to: '/whatif', label: '🔄 What-If Analysis' },
  { to: '/sql', label: '🗄️ SQL Insights' },
  { to: '/about', label: 'ℹ️ About' },
];

export default function Sidebar() {
  return (
    <aside style={{ width: '220px', background: '#16213e', padding: '16px 0', display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            display: 'block',
            padding: '10px 20px',
            color: isActive ? '#e94560' : '#ccc',
            textDecoration: 'none',
            fontWeight: isActive ? 600 : 400,
            background: isActive ? 'rgba(233,69,96,0.1)' : 'transparent',
            borderLeft: isActive ? '3px solid #e94560' : '3px solid transparent',
            fontSize: '0.88rem',
          })}
        >
          {label}
        </NavLink>
      ))}
    </aside>
  );
}
