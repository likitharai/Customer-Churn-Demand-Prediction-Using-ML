import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthProvider';
import { saasApi } from '../services/saasApi';
import PageErrorBoundary from './PageErrorBoundary';

export default function WorkspaceLayoutLive() {
  const { user, logout } = useAuth();
  const [workspace, setWorkspace] = useState(null);
  const [workspaceError, setWorkspaceError] = useState('');
  const [refreshVersion, setRefreshVersion] = useState(0);
  const location = useLocation();

  useEffect(() => {
    let active = true;
    saasApi('/api/workspace/me')
      .then(data => { if (active) { setWorkspace(data); setWorkspaceError(''); } })
      .catch(error => { if (active) setWorkspaceError(error.message); });
    return () => { active = false; };
  }, []);

  const refresh = () => setRefreshVersion(value => value + 1);
  const role = workspace?.role || user?.role;
  const agent = [['/', 'D', 'My dashboard'], ['/risk', 'R', 'My risk queue'], ['/customers', 'C', 'My customers'], ['/interactions', 'I', 'Interactions'], ['/tasks', 'T', 'My tasks'], ['/playbooks', 'P', 'Playbooks']];
  const manager = [['/', 'D', 'Portfolio overview'], ['/risk', 'R', 'Risk queue'], ['/customers', 'C', 'Customers'], ['/interactions', 'I', 'Team interactions'], ['/tasks', 'T', 'Team tasks'], ['/playbooks', 'P', 'Playbooks'], ['/manager', 'A', 'Team analytics'], ['/imports', 'U', 'Data imports']];
  const admin = [...manager, ['/admin', 'S', 'Workspace admin']];
  const links = role === 'admin' ? admin : role === 'manager' ? manager : agent;
  const title = links.find(item => item[0] === location.pathname)?.[2] || 'Customer profile';

  return <div className={`saas-shell role-${role || 'loading'}`}>
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">R</span><span>Retain<b>IQ</b></span></div>
      <div className="tenant-card"><small>{String(role || 'employee').toUpperCase()} WORKSPACE</small><strong>{workspace?.organization?.name || 'Loading...'}</strong><span>{workspace?.organization?.plan || '-'} plan</span></div>
      <nav>{links.map(([to, icon, label]) => <NavLink key={to} to={to} end={to === '/'}><span className="nav-icon">{icon}</span>{label}<span className="nav-arrow">›</span></NavLink>)}</nav>
      <div className="sidebar-card"><span className="pulse-dot"/>Connected<small>Each page loads current data when opened</small></div>
      <button className="logout-button" onClick={logout}>Log out</button>
    </aside>
    <section className="workspace">
      <header className="topbar"><div><p className="eyebrow">{role === 'agent' ? 'ASSIGNED CUSTOMER WORKSPACE' : role === 'manager' ? 'TEAM RETENTION ANALYTICS' : 'WORKSPACE GOVERNANCE'}</p><h1>{title}</h1></div><div className="top-actions"><button className="refresh-button" onClick={refresh}>Refresh page</button><div className="profile"><div className="avatar">{user?.full_name?.[0] || 'U'}</div><div><strong>{user?.full_name}</strong><span>{role}</span></div></div></div></header>
      <main className="content">
        {workspaceError && <div className="form-error">{workspaceError}</div>}
        <PageErrorBoundary key={`${location.pathname}:${refreshVersion}`}><Outlet context={{ workspace, role, user, refresh }}/></PageErrorBoundary>
      </main>
    </section>
  </div>;
}

