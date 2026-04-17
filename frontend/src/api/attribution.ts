import { apiFetch } from './client';
import type { TopDriver, AttributionItem } from '../types';

export const getTopDrivers = (params: {
  start_date: string;
  end_date: string;
}) => apiFetch<TopDriver[]>('/attribution/top-drivers', params);

export const getAttributionByService = (
  cloud: string,
  service: string,
  params: {
    start_date: string;
    end_date: string;
  }
) => apiFetch<AttributionItem[]>(`/attribution/${cloud}/${service}`, params);

export const getAttributionServices = () => apiFetch<string[]>('/attribution/services');
