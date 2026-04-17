import { useState, useEffect } from 'react';
import { getTopDrivers, getAttributionByService } from '../api/attribution';
import { useFilterContext } from '../context/FilterContext';
import type { TopDriver, AttributionItem } from '../types';

export const useAttribution = (selectedCloud?: string, selectedService?: string) => {
  const { startDate, endDate, cloud } = useFilterContext();
  
  const [topDrivers, setTopDrivers] = useState<TopDriver[]>([]);
  const [attributionData, setAttributionData] = useState<AttributionItem[]>([]);
  const [loadingTopDrivers, setLoadingTopDrivers] = useState(false);
  const [loadingAttribution, setLoadingAttribution] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchTopDrivers = async () => {
      setLoadingTopDrivers(true);
      setError(null);
      try {
        const p = { 
          start_date: startDate, 
          end_date: endDate,
          ...(cloud !== 'all' ? { cloud_provider: cloud } : {})
        };
        const data = await getTopDrivers(p);
        setTopDrivers(data);
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        setLoadingTopDrivers(false);
      }
    };
    fetchTopDrivers();
  }, [startDate, endDate, cloud]);

  useEffect(() => {
    const fetchAttribution = async () => {
      if (!selectedCloud || !selectedService) {
        setAttributionData([]);
        return;
      }
      setLoadingAttribution(true);
      try {
        const data = await getAttributionByService(selectedCloud, selectedService, {
          start_date: startDate,
          end_date: endDate
        });
        setAttributionData(data);
      } catch (err) {
        console.error(err);
      } finally {
         setLoadingAttribution(false);
      }
    };
    fetchAttribution();
  }, [startDate, endDate, selectedCloud, selectedService]);

  return { topDrivers, attributionData, loadingTopDrivers, loadingAttribution, error };
};
