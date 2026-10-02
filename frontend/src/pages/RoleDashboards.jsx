import React, { useCallback, useEffect, useState } from 'react';
import { saasApi } from '../services/saasApi';
import { AdminDecisionCharts, ManagerDecisionCharts } from '../components/DecisionCharts';

function useData(url, initial) {
  const [data, setData] = useState(initial);
  const [error, setError] = useState('');
  useEffect(() => { let active = true; saasApi(url).then(value => { if (active) setData(value); }).catch(reason => { if (active) setError(reason.message); }); return () => { active = false; }; }, [url]);
  return { data, error };
}

export function ManagerDashboard() {
  const metrics = useData('/api/workspace/metrics', {});
  const analytics = useData('/api/workspace/manager-analytics', { members: [] });
  return <div><section className="page-heading"><div><p className="eyebrow">MANAGER VIEW</p><h2>Team retention analytics</h2><p>Portfolio outcomes, workloads and customer activity across your team.</p></div></section>{(metrics.error || analytics.error) && <div className="form-error">{metrics.error || analytics.error}</div>}<section className="metric-grid">{[['Portfolio customers', metrics.data.customers], ['High risk', metrics.data.high_risk], ['Revenue at risk', `$${Number(metrics.data.revenue_at_risk || 0).toLocaleString()}`], ['Unassigned', analytics.data.unassigned_customers || 0]].map(([label, value]) => <article key={label}><div><p>{label}</p><strong>{value ?? '-'}</strong><small>Organization scope</small></div></article>)}</section><ManagerDecisionCharts members={analytics.data.members} unassigned={analytics.data.unassigned_customers || 0} totalCustomers={metrics.data.customers || 0}/><section className="panel"><div className="panel-head"><div><p className="eyebrow">TEAM PERFORMANCE</p><h3>Workload and activity</h3></div><span className="live-pill">{analytics.data.total_interactions || 0} interactions</span></div><div className="team-analytics"><div className="team-head"><span>Employee</span><span>Role</span><span>Customers</span><span>Open tasks</span><span>Interactions</span></div>{analytics.data.members.map(member => <div key={member.id}><span><i className="mini-avatar">{member.full_name?.[0] || 'U'}</i><b>{member.full_name}<small>{member.email}</small></b></span><span className="role-pill">{member.role}</span><strong>{member.assigned_customers}</strong><strong>{member.open_tasks}</strong><strong>{member.interactions}</strong></div>)}</div></section></div>;
}

export function AdminDashboard() {
  const [members, setMembers] = useState([]);
  const [models, setModels] = useState([]);
  const [audits, setAudits] = useState([]);
  const [form, setForm] = useState({ email: '', role: 'agent' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const [memberRows, modelRows, auditRows] = await Promise.all([saasApi('/api/workspace/members'), saasApi('/api/workspace/models'), saasApi('/api/workspace/audit')]);
      setMembers(memberRows); setModels(modelRows); setAudits(auditRows);
    } catch (reason) { setError(reason.message); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const invite = async event => {
    event.preventDefault(); setError(''); setResult(null); setBusy(true);
    try {
      const response = await saasApi('/api/workspace/invitations', { method: 'POST', body: JSON.stringify(form) });
      setResult(response); setForm({ email: '', role: 'agent' }); await load();
    } catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  };
  const delivery = result?.email_delivery;
  return <div><section className="page-heading"><div><p className="eyebrow">ADMIN VIEW · INVITATION-ONLY ACCESS</p><h2>Workspace administration</h2><p>Invite employees at their real work email, assign roles and review governance events.</p></div></section><form className="quick-create" onSubmit={invite}><input type="email" required placeholder="employee@company.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}/><select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}><option value="agent">Agent</option><option value="manager">Manager</option><option value="admin">Admin</option></select><button className="primary-button compact" disabled={busy}>{busy ? 'Sending...' : 'Send employee invitation'}</button></form>{error && <div className="form-error">{error}</div>}{result && <div className={`invite-token delivery-${delivery?.status}`}><strong>{delivery?.status === 'sent' ? delivery.detail : 'Email was not sent automatically'}</strong>{delivery?.status !== 'sent' && <span>{delivery?.detail}. Configure SMTP, or securely share this one-time link:</span>}<code>{result.invitation_url}</code><button className="text-button" onClick={() => navigator.clipboard?.writeText(result.invitation_url)}>Copy link</button></div>}<AdminDecisionCharts members={members} audits={audits} models={models}/><section className="admin-columns"><article className="panel"><div className="panel-head"><h3>Employees</h3><span className="live-pill">{members.length} seats</span></div><div className="member-list">{members.map(member => <div key={member.id}><i className="mini-avatar">{member.full_name?.[0] || 'U'}</i><strong>{member.full_name}<small>{member.email}</small></strong><span className="role-pill">{member.role}</span></div>)}</div></article><article className="panel"><div className="panel-head"><h3>Production models</h3></div>{models.map(model => <div className="model-row" key={model.id}><span className="pulse-dot"/><strong>{model.version}</strong><span>{model.status}</span></div>)}</article></section><section className="panel audit-panel"><div className="panel-head"><h3>Audit events</h3><span className="live-pill">{audits.length}</span></div>{audits.slice(0, 30).map(event => <div key={event.id}><strong>{event.action}</strong><span>{event.entity_type || 'workspace'}</span><time>{new Date(event.created_at).toLocaleString()}</time></div>)}</section></div>;
}


