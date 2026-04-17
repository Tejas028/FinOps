import { useState, useEffect, useCallback } from 'react';
import { getAlerts, getAlertsSummary } from '../api/alerts';
import { useFilterContext } from '../context/FilterContext';
import type { AlertListItem, AlertSummary, PaginatedResponse } from '../types';

export function useAlerts() {
  const { startDate, endDate, cloud } = useFilterContext();
  const [alerts, setAlerts] = useState<PaginatedResponse<AlertListItem> | null>(null);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await getAlertsSummary({ start_date: startDate, end_date: endDate });
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch alerts summary:', err);
    }
  }, [startDate, endDate]);

  const fetchAlerts = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const data = await getAlerts({
        start_date: startDate,
        end_date: endDate,
        cloud_provider: cloud === 'all' ? undefined : cloud,
        page,
        page_size: 20
      });
      setAlerts(data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, cloud]);

  useEffect(() => {
    fetchSummary();
    fetchAlerts();
  }, [fetchSummary, fetchAlerts]);

  return { alerts, summary, loading, fetchAlerts, refreshSummary: fetchSummary };
}
