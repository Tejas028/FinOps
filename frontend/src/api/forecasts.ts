import { apiFetch } from './client';
import type { PaginatedResponse, ForecastItem, BudgetRisk } from '../types';

export const getForecasts = (params: {
  cloud_provider?: string;
  service?: string;
  horizon_days?: number;
  page?: number;
  page_size?: number;
}) => apiFetch<PaginatedResponse<ForecastItem>>('/forecasts', params);

export const getLatestForecasts = (params: {
  cloud_provider?: string;
  service?: string;
  horizon_days?: number;
}) => apiFetch<ForecastItem[]>('/forecasts/latest', params);

export const getBudgetRisk = (params: {
  cloud_provider?: string;
  monthly_budget_usd?: number;
}) => apiFetch<BudgetRisk>('/forecasts/budget-risk', params);
