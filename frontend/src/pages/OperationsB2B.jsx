import React, { useCallback, useEffect, useState } from 'react';
import { Link, useOutletContext, useParams } from 'react-router-dom';
import { saasApi } from '../services/saasApi';

function useLoad(url, initial = []) {
  const [data, setData] = useState(initial);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setError('');
    setLoading(true);
    try { setData(await saasApi(url)); }
    catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }, [url]);
  useEffect(() => { load(); }, [load]);
  return { data, error, loading, load };
}

const Empty = ({ children }) => <div className="empty-state">{children}</div>;
const ErrorBox = ({ message }) => message ? <div className="form-error">{message}</div> : null;
const Loading = () => <div className="empty-state">Loading workspace data...</div>;

export function Overview() {
  const metrics = useLoad('/api/workspace/metrics', {});
  const tasks = useLoad('/api/workspace/tasks');
  const m = metrics.data;
  return <div>
    <section className="welcome-row"><div><p className="eyebrow">WORKSPACE DATA</p><h2>Your retention operation at a glance.</h2><p>Prioritize customer value, risk and follow-up urgency.</p></div><Link to="/risk" className="primary-button compact">Open risk queue</Link></section>
    <ErrorBox message={metrics.error || tasks.error}/>
    {metrics.loading ? <Loading/> : <section className="metric-grid">{[
      ['Customers', m.customers, 'Accounts in workspace'], ['High risk', m.high_risk, 'Need intervention'],
      ['Revenue at risk', `$${Number(m.revenue_at_risk || 0).toLocaleString()}`, 'Model-weighted'], ['Open tasks', m.open_tasks, 'Team follow-ups']
    ].map(([label, value, note]) => <article key={label}><div><p>{label}</p><strong>{value ?? '-'}</strong><small>{note}</small></div></article>)}</section>}
    <section className="dashboard-grid"><article className="panel span-2"><div className="panel-head"><h3>Retention performance</h3></div><div className="outcome-banner"><div><span>Retention success</span><strong>{m.retention_success_rate || 0}%</strong></div><div><span>Revenue protected</span><strong>${Number(m.revenue_protected || 0).toLocaleString()}</strong></div></div></article><article className="panel"><div className="panel-head"><h3>Next tasks</h3><Link to="/tasks">View all</Link></div>{tasks.loading ? <Loading/> : tasks.data.length ? tasks.data.slice(0, 4).map(item => <div className="mini-task" key={item.id}><i className={`priority ${item.priority}`}/><div><strong>{item.title}</strong><small>{item.customer_id || 'General'} · {item.status}</small></div></div>) : <Empty>No pending tasks.</Empty>}</article></section>
  </div>;
}

export function RiskQueue() {
  const rows = useLoad('/api/workspace/risk-queue');
  return <div><section className="page-heading"><div><p className="eyebrow">RISK × VALUE × URGENCY</p><h2>Customer risk queue</h2><p>Predictions are created automatically when customer data is imported.</p></div></section><ErrorBox message={rows.error}/>{rows.loading ? <Loading/> : <section className="panel table-wrap"><div className="data-grid risk-head"><span>Customer</span><span>Risk</span><span>Probability</span><span>Revenue at risk</span><span>Priority</span><span/></div>{rows.data.map(row => <div className="data-grid" key={row.customer_id}><Link to={`/customers/${row.customer_id}`}><strong>{row.customer_id}</strong><small>{row.contract || 'No contract'}</small></Link><span className={`risk-pill ${row.risk_level.toLowerCase().replace(' ', '-')}`}>{row.risk_level}</span><span>{Math.round(row.probability * 100)}%</span><span>${Number(row.revenue_at_risk).toLocaleString()}</span><strong>{Number(row.priority_score).toLocaleString()}</strong><span className="live-pill">{row.risk_source === 'outcome' ? 'Updated by follow-up' : row.risk_source === 'interaction' ? 'Updated by interaction' : 'ML score'}</span></div>)}{!rows.data.length && <Empty>Import customers to create your risk queue.</Empty>}</section>}</div>;
}

export function Customers() {
  const rows = useLoad('/api/workspace/risk-queue');
  const { role } = useOutletContext();
  return <div><section className="page-heading"><div><p className="eyebrow">CUSTOMER 360</p><h2>Customer portfolio</h2><p>Account health, ownership and value in one place.</p></div>{role !== 'agent' && <Link className="primary-button compact" to="/imports">Import customers</Link>}</section><ErrorBox message={rows.error}/>{rows.loading ? <Loading/> : <section className="customer-cards">{rows.data.map(row => <Link to={`/customers/${row.customer_id}`} className="customer-card" key={row.customer_id}><div className="customer-avatar">{row.customer_id.slice(0, 2)}</div><div><strong>{row.customer_id}</strong><span>{row.contract || 'Contract unavailable'}</span></div><div><small>Monthly value</small><b>${row.monthly_charges}</b></div><span className={`risk-pill ${row.risk_level.toLowerCase().replace(' ', '-')}`}>{row.risk_level}</span></Link>)}{!rows.data.length && <Empty>No customers in this workspace yet.</Empty>}</section>}</div>;
}

export function CustomerProfile() {
  const { id } = useParams();
  const profile = useLoad(`/api/workspace/customers/${id}`, null);
  const score = async () => { await saasApi(`/api/workspace/customers/${id}/score`, { method: 'POST' }); profile.load(); };
  if (profile.loading) return <Loading/>;
  if (!profile.data) return <ErrorBox message={profile.error || 'Customer unavailable'}/>;
  const data = profile.data, customer = data.customer, prediction = data.predictions[0], currentRisk = data.current_risk || { probability: prediction?.probability || 0, ml_probability: prediction?.probability || 0, risk_level: prediction?.risk_level || 'Unscored', source: 'ml' };
  return <div><section className="profile-hero"><div className="customer-avatar large">{id.slice(0, 2)}</div><div><p className="eyebrow">CUSTOMER PROFILE</p><h2>{id}</h2><span>{customer.contract} · {customer.internet_service || 'No internet service'} · {customer.tenure || 0} months</span></div><button className="primary-button compact" onClick={score}>Run prediction</button></section><section className="metric-grid"><article><div><p>Current operational risk</p><strong>{prediction ? `${Math.round(currentRisk.probability * 100)}%` : 'Unscored'}</strong><small>{currentRisk.source === 'outcome' ? `Updated by follow-up · ML baseline ${Math.round(currentRisk.ml_probability * 100)}%` : currentRisk.source === 'interaction' ? `Updated by interaction · ML baseline ${Math.round(currentRisk.ml_probability * 100)}%` : `${currentRisk.risk_level} · ML prediction`}</small></div></article><article><div><p>Monthly charges</p><strong>${customer.monthly_charges || 0}</strong><small>${customer.total_charges || 0} lifetime</small></div></article><article><div><p>Interactions</p><strong>{data.interactions.length}</strong><small>Recorded touchpoints</small></div></article><article><div><p>Open tasks</p><strong>{data.tasks.filter(item => item.status !== 'completed').length}</strong><small>Pending action</small></div></article></section></div>;
}

export function Tasks() {
  const rows = useLoad('/api/workspace/tasks');
  const [form, setForm] = useState({ title: '', customer_id: '', priority: 'medium' });
  const add = async event => { event.preventDefault(); await saasApi('/api/workspace/tasks', { method: 'POST', body: JSON.stringify({ ...form, customer_id: form.customer_id || null }) }); setForm({ title: '', customer_id: '', priority: 'medium' }); rows.load(); };
  const complete = async id => { await saasApi(`/api/workspace/tasks/${id}/complete`, { method: 'PATCH' }); rows.load(); };
  return <div><section className="page-heading"><div><p className="eyebrow">ACTION MANAGEMENT</p><h2>Tasks and follow-ups</h2></div></section><form className="quick-create" onSubmit={add}><input required placeholder="Follow-up task" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}/><input placeholder="Customer ID" value={form.customer_id} onChange={e => setForm({ ...form, customer_id: e.target.value })}/><select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}><option>low</option><option>medium</option><option>high</option><option>urgent</option></select><button className="primary-button compact">Add task</button></form><ErrorBox message={rows.error}/>{rows.loading ? <Loading/> : <section className="panel task-list">{rows.data.map(item => <article key={item.id}><i className={`priority ${item.priority}`}/><div><strong>{item.title}</strong><small>{item.customer_id || 'General'} · {item.priority} priority</small></div><span className="status">{item.status}</span>{item.status !== 'completed' && <button className="text-button" onClick={() => complete(item.id)}>Complete</button>}</article>)}{!rows.data.length && <Empty>No tasks yet.</Empty>}</section>}</div>;
}

export function Interactions() {
  const rows = useLoad('/api/workspace/interactions');
  const [form, setForm] = useState({ customer_id: '', channel: 'email', subject: '', notes: '', sentiment: 'neutral', status: 'open' });
  const add = async event => { event.preventDefault(); await saasApi('/api/workspace/interactions', { method: 'POST', body: JSON.stringify({ ...form, customer_id: form.customer_id || null }) }); setForm({ ...form, subject: '', notes: '' }); rows.load(); };
  return <div><section className="page-heading"><div><p className="eyebrow">CUSTOMER SIGNALS</p><h2>Interaction timeline</h2></div></section><form className="interaction-form panel" onSubmit={add}><input placeholder="Customer ID" value={form.customer_id} onChange={e => setForm({ ...form, customer_id: e.target.value })}/><select value={form.channel} onChange={e => setForm({ ...form, channel: e.target.value })}><option>email</option><option>phone</option><option>chat</option><option>meeting</option></select><input required placeholder="Subject" value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })}/><select value={form.sentiment} onChange={e => setForm({ ...form, sentiment: e.target.value })}><option>positive</option><option>neutral</option><option>negative</option></select><textarea placeholder="Notes" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })}/><button className="primary-button compact">Log interaction</button></form><ErrorBox message={rows.error}/>{rows.loading ? <Loading/> : <section className="panel interaction-list">{rows.data.map(item => <article key={item.id}><span className="channel-icon">{item.channel[0].toUpperCase()}</span><div><div><strong>{item.subject}</strong><span className="status">{item.status}</span></div><p>{item.notes || 'No notes'}</p><small>{item.customer_id || 'General'} · {new Date(item.created_at).toLocaleString()}</small></div><span className={`sentiment-label ${item.sentiment}`}>{item.sentiment}</span></article>)}{!rows.data.length && <Empty>No interactions yet.</Empty>}</section>}</div>;
}

export function Playbooks() {
  const rows = useLoad('/api/workspace/playbooks');
  const { role } = useOutletContext();
  const [form, setForm] = useState({ name: '', trigger_risk: 'High', recommended_action: '' });
  const add = async event => { event.preventDefault(); await saasApi('/api/workspace/playbooks', { method: 'POST', body: JSON.stringify(form) }); setForm({ name: '', trigger_risk: 'High', recommended_action: '' }); rows.load(); };
  return <div><section className="page-heading"><div><p className="eyebrow">STANDARDIZED RETENTION</p><h2>Playbooks</h2></div></section>{['manager', 'admin'].includes(role) && <form className="quick-create" onSubmit={add}><input required placeholder="Playbook name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}/><select value={form.trigger_risk} onChange={e => setForm({ ...form, trigger_risk: e.target.value })}><option>Very High</option><option>High</option><option>Medium</option><option>Low</option></select><input required placeholder="Recommended action" value={form.recommended_action} onChange={e => setForm({ ...form, recommended_action: e.target.value })}/><button className="primary-button compact">Create</button></form>}<ErrorBox message={rows.error}/>{rows.loading ? <Loading/> : <section className="playbook-grid">{rows.data.map(item => <article className="panel" key={item.id}><span className={`risk-pill ${item.trigger_risk.toLowerCase().replace(' ', '-')}`}>{item.trigger_risk}</span><h3>{item.name}</h3><p>{item.description || 'Operational response playbook'}</p><div>{item.recommended_action}</div></article>)}</section>}</div>;
}

export function Imports() {
  const rows = useLoad('/api/workspace/imports');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const upload = async event => {
    const file = event.target.files[0]; if (!file) return;
    setBusy(true); setMessage('');
    try {
      const data = new FormData(); data.append('file', file);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/workspace/imports/customers`, { method: 'POST', credentials: 'include', body: data });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || 'Import failed');
      setMessage(`${body.rows_imported} customer rows imported.`); await rows.load();
    } catch (reason) { setMessage(reason.message); }
    finally { setBusy(false); event.target.value = ''; }
  };
  const remove = async item => {
    if (!window.confirm(`Delete the CSV import record for ${item.filename}?`)) return;
    try { const result = await saasApi(`/api/workspace/imports/${item.id}`, { method: 'DELETE' }); setMessage(result.message); await rows.load(); }
    catch (reason) { setMessage(reason.message); }
  };
  return <div><section className="page-heading"><div><p className="eyebrow">DATA OPERATIONS</p><h2>Customer imports</h2><p>Upload CSV customer data. Source files are processed in memory and are not stored on the server.</p></div><label className="primary-button compact file-button">{busy ? 'Importing...' : 'Choose CSV'}<input type="file" accept=".csv,text/csv" disabled={busy} onChange={upload}/></label></section><ErrorBox message={rows.error}/>{message && <div className="b2b-note"><strong>Import update</strong><span>{message}</span></div>}{rows.loading ? <Loading/> : <section className="panel"><div className="data-grid import-head import-actions"><span>File</span><span>Rows</span><span>Status</span><span>Date</span><span>Action</span></div>{rows.data.map(item => <div className="data-grid import-head import-actions" key={item.id}><strong>{item.filename}</strong><span>{item.row_count}</span><span className="status">{item.status}</span><span>{new Date(item.created_at).toLocaleString()}</span><button className="danger-button" onClick={() => remove(item)}>Delete</button></div>)}{!rows.data.length && <Empty>No imports recorded.</Empty>}</section>}</div>;
}








