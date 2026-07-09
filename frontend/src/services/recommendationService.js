import { apiFetch } from './api';

export const getRecommendations = (customerData) =>
  apiFetch('/api/recommendation/generate', { method: 'POST', body: JSON.stringify(customerData) });
