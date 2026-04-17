import { apiFetch } from './client';
import type { PaginatedResponse, BillingSummary, SpendByDimension, TrendPoint } from '../types';

export const getBillingSummary = (params: {
  start_date: string;
  end_date: string;
  cloud_provider?: string;
  page?: number;
  page_size?: number;
}) => apiFetch<PaginatedResponse<BillingSummary>>('/billing/summary', params);

export const getBillingByCloud = (params: {
  start_date: string;
  end_date: string;
}) => apiFetch<SpendByDimension[]>('/billing/by-cloud', params);

export const getBillingByService = (params: {
  start_date: string;
  end_date: string;
  top_n?: number;
}) => apiFetch<SpendByDimension[]>('/billing/by-service', params);

export const getBillingTrend = (params: {
  start_date: string;
  end_date: string;
  granularity?: string;
}) => apiFetch<TrendPoint[]>('/billing/trend', params);
