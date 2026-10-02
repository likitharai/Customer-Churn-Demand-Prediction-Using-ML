import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthProvider';
export default function SaasLayout() {
  const { user, logout } = useAuth(); const location = useLocation();
  const links = [['/','â—«','Overview'],['/interactions','â—Ž','Interactions'],['/customers','â™™','Customers'],['/prediction','âœ¦','AI Prediction'],['/recommendations','â—‡','Playbooks'],['/revenue','â†—','Revenue risk']];
  if (user?.role === 'admin') links.push(['/admin','âš™','Administration']);
  const title = links.find(([path]) => path === location.pathname)?.[2] || 'Intelligence';
  return <div className="saas-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark">R</span><span>Retain<b>IQ</b></span></div><div className="workspace-label">WORKSPACE</div><nav>{links.map(([to,icon,label]) => <NavLink key={to} to={to} end={to === '/'}><span className="nav-icon">{icon}</span>{label}<span className="nav-arrow">â€º</span></NavLink>)}</nav><div className="sidebar-card"><span className="pulse-dot" />AI engine online<small>Churn model v2.0</small></div><button className="logout-button" onClick={logout}><span className="nav-icon">â†ª</span>Log out</button></aside><section className="workspace"><header className="topbar"><div><p className="eyebrow">RETENTION COMMAND CENTER</p><h1>{title}</h1></div><div className="profile"><div className="avatar">{user?.full_name?.charAt(0)}</div><div><strong>{user?.full_name}</strong><span>{user?.role}</span></div></div></header><main className="content"><Outlet /></main></section></div>;
}

