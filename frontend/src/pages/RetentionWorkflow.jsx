import React, { useCallback, useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { saasApi } from '../services/saasApi';
import '../retention-workflow.css';


function useWorkflowRows(url) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setData(await saasApi(url)); }
    catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  }, [url]);
  useEffect(() => { load(); }, [load]);
  return { data, loading, error, load };
}


const interactionDefaults = {
  customer_id: '', channel: 'phone', subject: '', notes: '', sentiment: 'neutral',
  problem_category: 'price', cancellation_intent: 'medium', requested_solution: '',
  reaction: 'neutral', follow_up_required: true, follow_up_at: '',
};


export function InteractionsWorkflow() {
  const [page, setPage] = useState(1);
  const rows = useWorkflowRows(`/api/workspace/workflow/interactions?page=${page}&page_size=50`);
  const interactionRows = rows.data.items || [];
  const [form, setForm] = useState(interactionDefaults);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      const result = await saasApi('/api/workspace/workflow/interactions', {
        method: 'POST',
        body: JSON.stringify({ ...form, follow_up_at: form.follow_up_at ? new Date(form.follow_up_at).toISOString() : null }),
      });
      const before = Math.round((result.interaction.base_probability || 0) * 100);
      const after = Math.round((result.interaction.operational_probability || 0) * 100);
      setMessage(result.follow_up ? `Interaction saved. Follow-up #${result.follow_up.id} created automatically. Operational risk: ${before}% → ${after}%.` : `Interaction saved. Operational risk: ${before}% → ${after}%.`);
      setForm(interactionDefaults); await rows.load();
    } catch (reason) { setMessage(reason.message); }
    finally { setBusy(false); }
  };
  return <div>
    <section className="page-heading"><div><p className="eyebrow">CUSTOMER DISCOVERY</p><h2>Team interactions</h2><p>Capture the customer problem and reaction. A connected follow-up is created automatically when action is required.</p></div></section>
    <form className="workflow-form panel" onSubmit={submit}>
      <div className="workflow-section-title"><span>1</span><div><strong>Customer and conversation</strong><small>Who was contacted and what happened?</small></div></div>
      <label>Customer ID<input required value={form.customer_id} onChange={event => setForm({ ...form, customer_id: event.target.value })} placeholder="TEST-0001"/></label>
      <label>Channel<select value={form.channel} onChange={event => setForm({ ...form, channel: event.target.value })}><option value="phone">Phone</option><option value="email">Email</option><option value="chat">Chat</option><option value="meeting">Meeting</option></select></label>
      <label className="span-2">Subject<input required value={form.subject} onChange={event => setForm({ ...form, subject: event.target.value })} placeholder="Customer considering cancellation"/></label>
      <div className="workflow-section-title"><span>2</span><div><strong>Problem and intent</strong><small>Structured signals update operational risk.</small></div></div>
      <label>Primary problem<select value={form.problem_category} onChange={event => setForm({ ...form, problem_category: event.target.value })}><option value="price">Price too high</option><option value="service">Service problem</option><option value="competitor">Competitor offer</option><option value="features">Missing features</option><option value="billing">Billing issue</option><option value="contract">Contract concern</option><option value="other">Other</option></select></label>
      <label>Cancellation intent<select value={form.cancellation_intent} onChange={event => setForm({ ...form, cancellation_intent: event.target.value })}><option value="none">None</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
      <label>Sentiment<select value={form.sentiment} onChange={event => setForm({ ...form, sentiment: event.target.value })}><option value="positive">Positive</option><option value="neutral">Neutral</option><option value="negative">Negative</option></select></label>
      <label>Reaction<select value={form.reaction} onChange={event => setForm({ ...form, reaction: event.target.value })}><option value="negative">Negative</option><option value="neutral">Neutral</option><option value="interested">Interested in an offer</option><option value="positive">Positive</option></select></label>
      <label className="span-2">Requested solution<input value={form.requested_solution} onChange={event => setForm({ ...form, requested_solution: event.target.value })} placeholder="Lower monthly bill or plan change"/></label>
      <label className="span-2">Conversation notes<textarea value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} placeholder="Describe the customer's concern in their own words."/></label>
      <div className="workflow-section-title"><span>3</span><div><strong>Next action</strong><small>Connect this conversation to a follow-up.</small></div></div>
      <label className="check-label"><input type="checkbox" checked={form.follow_up_required} onChange={event => setForm({ ...form, follow_up_required: event.target.checked })}/><span><strong>Create follow-up automatically</strong><small>Priority and recommended action are selected from the customer signals.</small></span></label>
      <label>Follow-up date<input type="datetime-local" disabled={!form.follow_up_required} value={form.follow_up_at} onChange={event => setForm({ ...form, follow_up_at: event.target.value })}/></label>
      <button className="primary-button workflow-submit" disabled={busy}>{busy ? 'Saving workflow...' : 'Log interaction and create follow-up'}</button>
    </form>
    {message && <div className="b2b-note"><strong>Workflow update</strong><span>{message}</span></div>}
    {rows.error && <div className="form-error">{rows.error}</div>}
    <section className="panel linked-list"><div className="panel-head"><div><p className="eyebrow">CONNECTED JOURNEYS</p><h3>Recent customer signals</h3></div><span className="live-pill">{rows.data.total || 0} interactions</span></div>
      {rows.loading ? <div className="empty-state">Loading interactions...</div> : interactionRows.map(item => <article key={item.id}>
        <span className="channel-icon">{item.channel?.[0]?.toUpperCase()}</span>
        <div className="journey-main"><div><Link to={`/customers/${item.customer_id}`}><strong>{item.subject}</strong></Link><span className={`sentiment-label ${item.sentiment}`}>{item.sentiment}</span></div><p>{item.notes || 'No conversation notes'}</p><small>{item.customer_id} · {item.problem_category || 'General'} · cancellation intent {item.cancellation_intent || 'none'} · {new Date(item.created_at).toLocaleString()}</small>
          <div className="risk-shift"><span>ML risk <b>{Math.round((item.base_probability || 0) * 100)}%</b></span><i>→</i><span>Operational risk <b>{Math.round((item.operational_probability || 0) * 100)}%</b></span></div>
          {item.follow_up && <Link className="follow-up-link" to="/tasks">Follow-up #{item.follow_up.id}: {item.follow_up.title} · {item.follow_up.status}</Link>}
        </div>
      </article>)}
      {!rows.loading && !rows.data.total || 0 && <div className="empty-state">No connected interactions yet.</div>}
    </section>
  </div>;
}


const assignmentDefaults = { customer_id: '', assigned_user_id: '', title: '', description: '', priority: 'high', due_at: '' };
const resolutionDefaults = { customer_response: 'offer_accepted', offer_type: 'Loyalty discount', offer_cost: 0, offer_duration: '6 months', final_sentiment: 'positive', notes: '', next_follow_up_at: '' };


export function TasksWorkflow() {
  const { role } = useOutletContext();
  const canAssign = role === 'manager' || role === 'admin';
  const rows = useWorkflowRows('/api/workspace/workflow/tasks');
  const [agents, setAgents] = useState([]);
  const [assignment, setAssignment] = useState(assignmentDefaults);
  const [active, setActive] = useState(null);
  const [form, setForm] = useState(resolutionDefaults);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (canAssign) saasApi('/api/workspace/members').then(items => setAgents(items.filter(item => item.role === 'agent' && item.is_active))).catch(reason => setMessage(reason.message));
  }, [canAssign]);
  const assignTask = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      const result = await saasApi('/api/workspace/workflow/tasks', { method: 'POST', body: JSON.stringify({ ...assignment, assigned_user_id: Number(assignment.assigned_user_id), due_at: assignment.due_at ? new Date(assignment.due_at).toISOString() : null }) });
      setMessage(`Follow-up #${result.id} assigned to ${result.assigned_to.full_name}. Only that Agent can see it.`);
      setAssignment(assignmentDefaults); await rows.load();
    } catch (reason) { setMessage(reason.message); }
    finally { setBusy(false); }
  };
  const resolve = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      const result = await saasApi(`/api/workspace/workflow/tasks/${active.id}/resolve`, { method: 'POST', body: JSON.stringify({ ...form, offer_cost: Number(form.offer_cost || 0), next_follow_up_at: form.next_follow_up_at ? new Date(form.next_follow_up_at).toISOString() : null }) });
      const outcome = result.outcome;
      setMessage(`Outcome saved. Operational risk is ${Math.round((outcome.operational_probability || 0) * 100)}%. Protected revenue: $${Number(outcome.revenue_protected || 0).toLocaleString()}; expected net value: $${Number(outcome.expected_net_value || 0).toLocaleString()}.`);
      setActive(null); setForm(resolutionDefaults); await rows.load();
    } catch (reason) { setMessage(reason.message); }
    finally { setBusy(false); }
  };
  return <div>
    <section className="page-heading"><div><p className="eyebrow">ACTION AND OUTCOME MANAGEMENT</p><h2>Tasks and follow-ups</h2><p>Resolve the action created from a customer interaction, record the response, and measure retained value.</p></div></section>
    {canAssign && <form className="manager-assignment-form panel" onSubmit={assignTask}><div className="workflow-section-title"><span>+</span><div><strong>Assign customer follow-up</strong><small>The selected task is visible only to the chosen Agent.</small></div></div><label>Customer ID<input required value={assignment.customer_id} onChange={event => setAssignment({ ...assignment, customer_id: event.target.value })} placeholder="DEMO-1001"/></label><label>Assign to Agent<select required value={assignment.assigned_user_id} onChange={event => setAssignment({ ...assignment, assigned_user_id: event.target.value })}><option value="">Select Agent</option>{agents.map(agent => <option key={agent.id} value={agent.id}>{agent.full_name} — {agent.email}</option>)}</select></label><label className="span-2">Follow-up task<input required value={assignment.title} onChange={event => setAssignment({ ...assignment, title: event.target.value })} placeholder="Present retention offer"/></label><label className="span-2">Recommended action<textarea value={assignment.description} onChange={event => setAssignment({ ...assignment, description: event.target.value })} placeholder="Offer an approved plan or discount based on the customer concern."/></label><label>Priority<select value={assignment.priority} onChange={event => setAssignment({ ...assignment, priority: event.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label><label>Due date<input type="datetime-local" value={assignment.due_at} onChange={event => setAssignment({ ...assignment, due_at: event.target.value })}/></label><button className="primary-button workflow-submit" disabled={busy || !agents.length}>{busy ? 'Assigning...' : 'Assign follow-up'}</button></form>}
    {message && <div className="b2b-note"><strong>Workflow update</strong><span>{message}</span></div>}
    {rows.error && <div className="form-error">{rows.error}</div>}
    <section className="panel follow-up-list">
      <div className="panel-head"><h3>Connected follow-ups</h3><span className="live-pill">{rows.data.filter(item => item.status !== 'completed').length} active</span></div>
      {rows.loading ? <div className="empty-state">Loading follow-ups...</div> : rows.data.map(item => <article key={item.id}>
        <i className={`priority ${item.priority}`}/><div className="follow-up-body"><div><strong>{item.title}</strong><span className="status">{item.status}</span></div><p>{item.suggested_action || item.description || 'Contact the customer and agree on the next step.'}</p><small>{item.customer_id || 'General'} · {item.priority} priority {item.assigned_to ? `· assigned to ${item.assigned_to.full_name}` : ''} {item.due_at ? `· due ${new Date(item.due_at).toLocaleString()}` : ''}</small>
          {item.interaction && <div className="source-signal"><span>Source interaction #{item.interaction.id}</span><b>{item.interaction.problem_category || 'customer concern'}</b><span>{item.interaction.reaction || 'neutral'} reaction</span><span>Operational risk {Math.round((item.interaction.operational_probability || 0) * 100)}%</span></div>}
        </div>{item.status !== 'completed' && <button className="primary-button compact" onClick={() => { setActive(item); setForm(resolutionDefaults); }}>Record response</button>}
      </article>)}
      {!rows.loading && !rows.data.length && <div className="empty-state">Log a customer interaction to create the first connected follow-up.</div>}
    </section>
    {active && <div className="modal-backdrop"><form className="modal outcome-modal" onSubmit={resolve}><div className="panel-head"><div><p className="eyebrow">FOLLOW-UP OUTCOME</p><h3>{active.customer_id}: {active.title}</h3></div><button type="button" className="close" onClick={() => setActive(null)}>×</button></div>
      <div className="outcome-context"><strong>Recommended action</strong><p>{active.suggested_action || active.description}</p>{active.interaction && <small>Started from interaction #{active.interaction.id} · {active.interaction.problem_category} concern</small>}</div>
      <div className="form-grid"><label>Customer response<select value={form.customer_response} onChange={event => setForm({ ...form, customer_response: event.target.value })}><option value="offer_accepted">Offer accepted</option><option value="offer_rejected">Offer rejected</option><option value="needs_time">Needs more time</option><option value="issue_resolved">Issue resolved</option><option value="customer_retained">Customer retained</option><option value="still_cancelling">Still plans to cancel</option><option value="customer_churned">Customer churned</option></select></label><label>Final sentiment<select value={form.final_sentiment} onChange={event => setForm({ ...form, final_sentiment: event.target.value })}><option value="positive">Positive</option><option value="neutral">Neutral</option><option value="negative">Negative</option></select></label>
        <label>Offer type<input value={form.offer_type} onChange={event => setForm({ ...form, offer_type: event.target.value })} placeholder="15% loyalty discount"/></label><label>Offer cost<input type="number" min="0" step="0.01" value={form.offer_cost} onChange={event => setForm({ ...form, offer_cost: event.target.value })}/></label><label>Offer duration<input value={form.offer_duration} onChange={event => setForm({ ...form, offer_duration: event.target.value })} placeholder="6 months"/></label><label>Next follow-up<input type="datetime-local" value={form.next_follow_up_at} onChange={event => setForm({ ...form, next_follow_up_at: event.target.value })}/></label><label className="full">Outcome notes<textarea value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} placeholder="What did the customer decide and why?"/></label></div>
      <button className="primary-button" disabled={busy}>{busy ? 'Calculating outcome...' : 'Save outcome and update operational risk'}</button>
    </form></div>}
  </div>;
}




