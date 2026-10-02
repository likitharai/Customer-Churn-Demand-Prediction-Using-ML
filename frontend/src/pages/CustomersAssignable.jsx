import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { saasApi } from '../services/saasApi';


function useRows(url, initial = []) {
  const [data, setData] = useState(initial);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setData(await saasApi(url)); }
    catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }, [url]);
  useEffect(() => { load(); }, [load]);
  return { data, error, loading, load };
}


export default function CustomersAssignable() {
  const { role } = useOutletContext();
  const customers = useRows('/api/workspace/risk-queue');
  const members = useRows('/api/workspace/members');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [message, setMessage] = useState('');
  const [savingId, setSavingId] = useState('');
  const canAssign = role === 'manager' || role === 'admin';
  const agents = canAssign ? members.data.filter(member => member.role === 'agent' && member.is_active) : [];
  const agentIds = new Set(agents.map(agent => agent.id));
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return term ? customers.data.filter(customer =>
      customer.customer_id.toLowerCase().includes(term) ||
      String(customer.risk_level).toLowerCase().includes(term) ||
      String(customer.contract || '').toLowerCase().includes(term)
    ) : customers.data;
  }, [customers.data, search]);
  const pageSize = 200;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const visible = filtered.slice((page - 1) * pageSize, page * pageSize);

  useEffect(() => { setPage(1); }, [search]);
  useEffect(() => { if (page > pageCount) setPage(pageCount); }, [page, pageCount]);

  const assign = async (customerId, value) => {
    setSavingId(customerId); setMessage('');
    try {
      await saasApi(`/api/workspace/customers/${customerId}/assignment`, {
        method: 'PUT',
        body: JSON.stringify({ assigned_user_id: value ? Number(value) : null }),
      });
      const assignee = agents.find(agent => agent.id === Number(value));
      setMessage(`${customerId} assigned to ${assignee?.full_name || 'the unassigned queue'}.`);
      await customers.load();
    } catch (reason) { setMessage(reason.message); }
    finally { setSavingId(''); }
  };

  return <div>
    <section className="page-heading"><div><p className="eyebrow">CUSTOMER 360</p><h2>{canAssign ? 'Customer assignments' : 'My customer portfolio'}</h2><p>{canAssign ? 'Search customers and distribute ownership to active Agents.' : 'Customers assigned to your employee account.'}</p></div>{canAssign && <Link className="primary-button compact" to="/imports">Import customers</Link>}</section>
    {(customers.error || (canAssign && members.error)) && <div className="form-error">{customers.error || members.error}</div>}
    {message && <div className="b2b-note"><strong>Assignment update</strong><span>{message}</span></div>}
    <section className="assignment-toolbar panel"><input type="search" placeholder="Search customer ID, risk or contract" value={search} onChange={event => setSearch(event.target.value)}/><span>{filtered.length.toLocaleString()} customers</span>{canAssign && <span>{agents.length} active Agents</span>}</section>
    {customers.loading ? <div className="empty-state">Loading customers...</div> : <section className="panel assignment-table">
      <div className="assignment-row assignment-head"><span>Customer</span><span>Risk</span><span>Monthly value</span><span>Contract</span>{canAssign && <span>Assigned Agent</span>}</div>
      {visible.map(customer => <div className="assignment-row" key={customer.customer_id}>
        <Link to={`/customers/${customer.customer_id}`}><strong>{customer.customer_id}</strong></Link>
        <span className={`risk-pill ${customer.risk_level.toLowerCase().replace(' ', '-')}`}>{customer.risk_level}</span>
        <strong>${Number(customer.monthly_charges || 0).toLocaleString()}</strong>
        <span>{customer.contract || '-'}</span>
        {canAssign && <select aria-label={`Assign ${customer.customer_id}`} disabled={savingId === customer.customer_id || members.loading} value={agentIds.has(customer.assigned_user_id) ? customer.assigned_user_id : ''} onChange={event => assign(customer.customer_id, event.target.value)}><option value="">Unassigned</option>{agents.map(agent => <option value={agent.id} key={agent.id}>{agent.full_name} — {agent.email}</option>)}</select>}
      </div>)}
      {!visible.length && <div className="empty-state">No matching customers.</div>}
      {filtered.length > pageSize && <div className="table-note"><button className="text-button" disabled={page === 1} onClick={() => setPage(value => value - 1)}>Previous</button><span>Page {page} of {pageCount} · rows {((page - 1) * pageSize + 1).toLocaleString()}–{Math.min(page * pageSize, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()}</span><button className="text-button" disabled={page === pageCount} onClick={() => setPage(value => value + 1)}>Next</button></div>}
      {canAssign && !agents.length && <div className="table-note">Invite at least one employee with the Agent role before assigning customers.</div>}
    </section>}
  </div>;
}


