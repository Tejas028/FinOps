import { useState, useEffect } from 'react';
import { getBillingSummary, getBillingByCloud, getBillingByService, getBillingTrend } from '../api/billing';
import { useFilterContext } from '../context/FilterContext';
import type { PaginatedResponse, BillingSummary, SpendByDimension, TrendPoint } from '../types';

export const useBilling = () => {
  const { startDate, endDate, cloud } = useFilterContext();
  
  const [summary, setSummary] = useState<PaginatedResponse<BillingSummary> | null>(null);
  const [byCloud, setByCloud] = useState<SpendByDimension[]>([]);
  const [byService, setByService] = useState<SpendByDimension[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { start_date: startDate, end_date: endDate, ...(cloud !== 'all' ? { cloud_provider: cloud } : {}) };
      
      const [sum, bCloud, bServ, trnd] = await Promise.all([
        getBillingSummary({ ...params, page: 1, page_size: 50 }),
        getBillingByCloud(params),
        getBillingByService({ ...params, top_n: 10 }),
        getBillingTrend({ ...params, granularity: 'day' })
      ]);
      
      setSummary(sum);
      setByCloud(bCloud);
      setByService(bServ);
      setTrend(trnd);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [startDate, endDate, cloud]);

  return { summary, byCloud, byService, trend, loading, error, refetch: fetchAll };
};
