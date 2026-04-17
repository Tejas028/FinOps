import { useState, useEffect, useCallback } from 'react';
import { getAnomalies, getAnomaliesSummary, getRecentAnomalies } from '../api/anomalies';
import { useFilterContext } from '../context/FilterContext';
import type { PaginatedResponse, AnomalyListItem, AnomalySummary } from '../types';

export const useAnomalies = (severity?: string) => {
  const { startDate, endDate, cloud } = useFilterContext();
  
  const [anomalies, setAnomalies] = useState<PaginatedResponse<AnomalyListItem> | null>(null);
  const [summary, setSummary] = useState<AnomalySummary | null>(null);
  const [recent, setRecent] = useState<AnomalyListItem[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAnomalies = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        start_date: startDate,
        end_date: endDate,
        ...(cloud !== 'all' ? { cloud_provider: cloud } : {}),
        ...(severity && severity !== 'all' ? { severity } : {}),
        page,
        page_size: 20
      };
      const data = await getAnomalies(params);
      setAnomalies(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, cloud, severity]);

  const fetchMetrics = useCallback(async () => {
    try {
      const p = { 
        start_date: startDate, 
        end_date: endDate,
        ...(cloud !== 'all' ? { cloud_provider: cloud } : {})
      };
      
      const [sum, rec] = await Promise.all([
        getAnomaliesSummary(p),
        getRecentAnomalies({ ...p, limit: 5 })
      ]);
      setSummary(sum);
      setRecent(rec);
    } catch (e) {
      console.error(e);
    }
  }, [startDate, endDate, cloud]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    fetchAnomalies(1);
  }, [fetchAnomalies]);

  return { anomalies, summary, recent, loading, error, fetchAnomalies };
};
