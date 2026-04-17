import { useState, useEffect, useCallback } from 'react';
import { getForecasts, getLatestForecasts, getBudgetRisk } from '../api/forecasts';
import { useFilterContext } from '../context/FilterContext';
import type { PaginatedResponse, ForecastItem, BudgetRisk } from '../types';

export const useForecasts = (horizonDays: number = 30, service?: string) => {
  const { cloud } = useFilterContext();
  
  const [forecastsPage, setForecastsPage] = useState<PaginatedResponse<ForecastItem> | null>(null);
  const [latestList, setLatestList] = useState<ForecastItem[]>([]);
  const [budgetRisk, setBudgetRisk] = useState<BudgetRisk | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchForecasts = useCallback(async (page = 1, pageSize = 25) => {
    setLoading(true);
    setError(null);
    try {
      const p = { 
        ...(cloud !== 'all' ? { cloud_provider: cloud } : {}), 
        ...(service ? { service } : {}),
        horizon_days: horizonDays 
      };
      
      const [fPage, latest] = await Promise.all([
        getForecasts({ ...p, page, page_size: pageSize }),
        getLatestForecasts(p)
      ]);
      
      setForecastsPage(fPage);
      setLatestList(latest);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [cloud, horizonDays, service]);

  const fetchBudgetRisk = useCallback(async (budgetUsd: number) => {
    if (!budgetUsd || budgetUsd <= 0) {
      setBudgetRisk(null);
      return;
    }
    try {
      const risk = await getBudgetRisk({
        ...(cloud !== 'all' ? { cloud_provider: cloud } : {}),
        monthly_budget_usd: budgetUsd
      });
      setBudgetRisk(risk);
    } catch (e: any) {
      // 404 means no forecasts available for this cloud — not an error
      if (e?.status === 404) {
        setBudgetRisk(null);
      } else {
        console.error('fetchBudgetRisk error:', e);
      }
    }
  }, [cloud]);

  useEffect(() => {
    fetchForecasts();
  }, [fetchForecasts]);

  return { forecastsPage, latestList, budgetRisk, setBudgetRisk, loading, error, fetchBudgetRisk, fetchForecasts };
};
