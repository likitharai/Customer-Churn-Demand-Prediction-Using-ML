import React, { useCallback, useEffect, useState } from 'react';
import { saasApi } from '../services/saasApi';


export default function ImportsAutomated() {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    try { setRows(await saasApi('/api/workspace/imports')); }
    catch (reason) { setError(reason.message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const upload = async event => {
    const file = event.target.files[0];
    if (!file) return;
    setBusy(true); setMessage(''); setError('');
    try {
      const data = new FormData(); data.append('file', file);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/workspace/imports/customers`, {
        method: 'POST',
        credentials: 'include',
        body: data,
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || 'Import failed');
      setMessage(`${body.rows_imported} customers imported and ${body.predictions_created} ML predictions created${body.scoring_errors ? ` (${body.scoring_errors} scoring errors)` : ''}.`);
      await load();
    } catch (reason) { setError(reason.message); }
    finally { setBusy(false); event.target.value = ''; }
  };

  const scoreAll = async () => {
    if (!window.confirm('Create a fresh ML prediction for every customer in this workspace?')) return;
    setBusy(true); setMessage('Scoring all customers. Keep this page open...'); setError('');
    try {
      const result = await saasApi('/api/workspace/imports/score-all', { method: 'POST' });
      setMessage(`${result.predictions_created} customers scored${result.scoring_errors ? `; ${result.scoring_errors} could not be scored` : ''}. The dashboard now uses these latest predictions.`);
    } catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  };

  const remove = async item => {
    if (!window.confirm(`Delete the CSV import record for ${item.filename}?`)) return;
    try { const result = await saasApi(`/api/workspace/imports/${item.id}`, { method: 'DELETE' }); setMessage(result.message); await load(); }
    catch (reason) { setError(reason.message); }
  };

  return <div><section className="page-heading"><div><p className="eyebrow">DATA + ML OPERATIONS</p><h2>Customer imports</h2><p>Every newly imported customer is scored automatically. Existing customers can be rescored in one operation.</p></div><div className="import-buttons"><button className="refresh-button" disabled={busy} onClick={scoreAll}>Score all existing customers</button><label className="primary-button compact file-button">{busy ? 'Processing...' : 'Choose CSV'}<input type="file" accept=".csv,text/csv" disabled={busy} onChange={upload}/></label></div></section>{error && <div className="form-error">{error}</div>}{message && <div className="b2b-note"><strong>Data operation</strong><span>{message}</span></div>}<section className="panel"><div className="data-grid import-head import-actions"><span>File</span><span>Rows</span><span>Status</span><span>Date</span><span>Action</span></div>{rows.map(item => <div className="data-grid import-head import-actions" key={item.id}><strong>{item.filename}</strong><span>{item.row_count}</span><span className="status">{item.status}</span><span>{new Date(item.created_at).toLocaleString()}</span><button className="danger-button" onClick={() => remove(item)}>Delete</button></div>)}{!rows.length && <div className="empty-state">No imports recorded.</div>}</section></div>;
}



