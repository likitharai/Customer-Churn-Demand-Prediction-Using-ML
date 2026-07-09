import React, { useState } from 'react';
import { predictChurn } from '../services/predictionService';

export default function Prediction() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    setLoading(true);
    const sample = { tenure: 12, MonthlyCharges: 70, TotalCharges: 840, Contract: 'Month-to-month', InternetService: 'Fiber optic' };
    const res = await predictChurn(sample);
    setResult(res);
    setLoading(false);
  };

  return (
    <div>
      <h2>Churn Prediction</h2>
      <p style={{ color: '#888', marginBottom: '24px' }}>Run single or batch churn prediction.</p>
      <button onClick={handlePredict} disabled={loading} style={{ padding: '10px 24px', background: '#e94560', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>
        {loading ? 'Predicting...' : 'Run Sample Prediction'}
      </button>
      {result && (
        <div style={{ marginTop: '24px', padding: '20px', background: '#fff', borderRadius: '12px', boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
          <p><strong>Prediction:</strong> {result.prediction_label}</p>
          <p><strong>Probability:</strong> {(result.probability * 100).toFixed(2)}%</p>
          <p><strong>Risk Level:</strong> {result.risk_level}</p>
        </div>
      )}
    </div>
  );
}
