import { apiFetch } from './client';

export const getHealth = () => apiFetch<{ status: string }>('/health');
