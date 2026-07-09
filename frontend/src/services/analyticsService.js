import { apiFetch } from './api';

export const getExecutiveKPIs = () => apiFetch('/api/analytics/kpis');
export const getChurnBySegment = () => apiFetch('/api/analytics/churn-by-segment');
export const getRevenueRisk = () => apiFetch('/api/revenue/summary');
