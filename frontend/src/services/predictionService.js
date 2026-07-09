import { apiFetch } from './api';

export const predictChurn = (customerData) =>
  apiFetch('/api/prediction/predict', { method: 'POST', body: JSON.stringify(customerData) });

export const predictBatch = (formData) =>
  apiFetch('/api/prediction/predict-batch', { method: 'POST', body: formData, headers: {} });
