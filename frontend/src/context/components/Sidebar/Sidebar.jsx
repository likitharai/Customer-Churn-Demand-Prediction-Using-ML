import React from 'react';
import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'ðŸ  Home' },
  { to: '/executive', label: 'ðŸ“Š Executive Dashboard' },
  { to: '/customers', label: 'ðŸ‘¥ Customer Analytics' },
  { to: '/prediction', label: 'ðŸ¤– Prediction' },
  { to: '/revenue', label: 'ðŸ’° Revenue Risk' },
  { to: '/recommendations', label: 'ðŸ’¡ Recommendations' },
  { to: '/shap', label: 'ðŸ” SHAP Analysis' },
  { to: '/whatif', label: 'ðŸ”„ What-If Analysis' },
  { to: '/sql', label: 'ðŸ—„ï¸ SQL Insights' },
  { to: '/about', label: 'â„¹ï¸ About' },
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

