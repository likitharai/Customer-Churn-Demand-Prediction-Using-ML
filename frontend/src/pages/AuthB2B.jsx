import React, { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthProvider';
import { saasApi } from '../services/saasApi';

export default function AuthB2B() {
  const { user, login } = useAuth();
  const [params] = useSearchParams();
  const token = params.get('invite');
  const [invitation, setInvitation] = useState(null);
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    saasApi(`/api/auth/invitation/${token}`)
      .then(data => { setInvitation(data); setForm(current => ({ ...current, email: data.email })); })
      .catch(reason => setError(reason.message));
  }, [token]);
  if (user) return <Navigate to="/" replace/>;

  const submit = async event => {
    event.preventDefault(); setBusy(true); setError('');
    try {
      if (token) {
        const data = await saasApi('/api/auth/accept-invitation', { method: 'POST', body: JSON.stringify({ token, full_name: form.full_name, password: form.password }) });
        window.location.assign('/');
      } else {
        await login(form);
      }
    } catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  };

  return <div className="auth-shell"><section className="auth-story"><div className="brand light"><span className="brand-mark">R</span><span>Retain<b>IQ</b></span></div><div className="story-content"><p className="eyebrow">B2B RETENTION INTELLIGENCE</p><h1>Decisions for every <em>customer signal.</em></h1><p>Imported customer data becomes an operating dashboard for risk, revenue, team action and retention outcomes.</p><div className="proof"><div><strong>Agent</strong><span>assigned portfolio</span></div><div><strong>Manager</strong><span>team analytics</span></div><div><strong>Admin</strong><span>governance</span></div></div></div></section><section className="auth-panel"><form className="auth-card" onSubmit={submit}><p className="eyebrow">{token ? 'EMPLOYEE INVITATION' : 'EMPLOYEE ACCESS'}</p><h2>{token ? 'Join your workspace' : 'Sign in to RetainIQ'}</h2><p>{token ? `${invitation?.organization || 'Your company'} invited you as ${invitation?.role || 'an employee'}.` : 'Access is invitation-only for authorized company employees.'}</p>{token && <label>Full name<input required value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })}/></label>}<label>Work email<input type="email" required readOnly={Boolean(token)} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}/></label><label>Password<input type="password" required minLength="12" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}/></label>{error && <div className="form-error">{error}</div>}<button className="primary-button" disabled={busy}>{busy ? 'Please wait...' : token ? 'Accept invitation' : 'Sign in'}<span>→</span></button>{!token && <div className="b2b-note"><strong>Need access?</strong><span>Ask your workspace administrator to invite your work email.</span></div>}</form></section></div>;
}



