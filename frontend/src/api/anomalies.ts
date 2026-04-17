import { apiFetch } from './client';
import type { PaginatedResponse, AnomalyListItem, AnomalySummary } from '../types';

export const getAnomalies = (params: {
  start_date?: string;
  end_date?: string;
  severity?: string;
  cloud_provider?: string;
  page?: number;
  page_size?: number;
}) => apiFetch<PaginatedResponse<AnomalyListItem>>('/anomalies', params);

export const getAnomaliesSummary = (params: {
  start_date: string;
  end_date: string;
}) => apiFetch<AnomalySummary>('/anomalies/summary', params);

export const getRecentAnomalies = (params: {
  limit?: number;
}) => apiFetch<AnomalyListItem[]>('/anomalies/recent', params);

export const getAnomalyDetails = (anomalyId: string) => 
  apiFetch<AnomalyListItem>(`/anomalies/${anomalyId}`);
