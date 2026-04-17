import { apiFetch } from './client';
import type { PaginatedResponse, AlertListItem, AlertSummary } from '../types';

export interface GetAlertsParams {
  start_date: string;
  end_date: string;
  severity?: string;
  cloud_provider?: string;
  alert_type?: string;
  is_resolved?: boolean;
  page?: number;
  page_size?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface GetAlertsSummaryParams {
  start_date: string;
  end_date: string;
  [key: string]: string | number | boolean | undefined;
}

export async function getAlerts(params: GetAlertsParams): Promise<PaginatedResponse<AlertListItem>> {
  return apiFetch<PaginatedResponse<AlertListItem>>('/alerts', params);
}

export async function getAlertsSummary(params: GetAlertsSummaryParams): Promise<AlertSummary> {
  return apiFetch<AlertSummary>('/alerts/summary', params as Record<string, string | number | boolean | undefined>);
}

export async function resolveAlert(alertId: string): Promise<{ resolved: boolean; alert_id: string }> {
  const response = await fetch(`http://localhost:8000/alerts/${alertId}/resolve`, {
    method: 'PATCH',
    headers: { 'Accept': 'application/json' }
  });
  if (!response.ok) {
    throw { status: response.status, message: await response.text() };
  }
  return response.json();
}
