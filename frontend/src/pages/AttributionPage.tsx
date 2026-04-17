import React, { useState, useEffect, useMemo } from 'react';
import { useAttribution } from '../hooks/useAttribution';
import { getAttributionServices } from '../api/attribution';
import { ShapDriversChart } from '../components/charts/ShapDriversChart';
import { SpendTrendChart } from '../components/charts/SpendTrendChart';
import { DataTable, ColumnDef } from '../components/shared/DataTable';
import { useFilterContext } from '../context/FilterContext';
import { EmptyState } from '../components/shared/EmptyState';
import type { AttributionItem } from '../types';

export const AttributionPage: React.FC = () => {
  const { cloud: globalCloud } = useFilterContext();
  const [selectedCloud, setSelectedCloud] = useState<string>(globalCloud === 'all' ? 'aws' : globalCloud);
  const [selectedService, setSelectedService] = useState<string>('');
  const [services, setServices] = useState<string[]>([]);
  const [loadingServices, setLoadingServices] = useState(false);

  const { topDrivers, attributionData, loadingTopDrivers, loadingAttribution } = useAttribution(
    selectedCloud, 
    selectedService
  );

  // Fetch services on mount
  useEffect(() => {
    let active = true;
    const fetchSvc = async () => {
      setLoadingServices(true);
      try {
        const data = await getAttributionServices();
        if (active) {
          setServices(data);
          if (data.length > 0 && !selectedService) {
            setSelectedService(data[0]);
          }
        }
      } catch (e) {
        console.error("Failed to fetch attribution services", e);
      } finally {
        if (active) setLoadingServices(false);
      }
    };
    fetchSvc();
    return () => { active = false; };
  }, [selectedService]);

  const tableColumns: ColumnDef<AttributionItem>[] = [
    { key: "date", header: "Date", render: (a) => a.attribution_date },
    { key: "cost", header: "Total Cost", render: (a) => `$${a.total_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "driver1", header: "Top Driver", render: (a) => a.top_driver_1 || '-' },
    { key: "val1", header: "SHAP Value", render: (a) => a.top_driver_1_value !== null ? a.top_driver_1_value.toFixed(2) : '-' },
    { key: "driver2", header: "#2 Driver", render: (a) => a.top_driver_2 || '-' },
    { key: "val2", header: "#2 Value", render: (a) => a.top_driver_2_value !== null ? a.top_driver_2_value.toFixed(2) : '-' },
  ];

  const trendData = useMemo(() => {
    return attributionData.map(d => ({
      period: d.attribution_date,
      total_cost_usd: d.total_cost_usd,
      record_count: 0
    }));
  }, [attributionData]);

  return (
    <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
      
      {/* Left Panel: Top Drivers */}
      <div style={{ flex: '1 1 35%', minWidth: '300px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>Global Top Cost Drivers</h2>
          {loadingTopDrivers && topDrivers.length === 0 ? (
            <div style={{ height: '180px' }} />
          ) : (
            <>
              <ShapDriversChart data={topDrivers} />
              
              <table style={{ width: '100%', marginTop: '24px', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr>
                    <th style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)', fontWeight: 500, color: 'var(--text-secondary)' }}>Driver</th>
                    <th style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border)', fontWeight: 500, color: 'var(--text-secondary)', textAlign: 'right' }}>Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {topDrivers.slice(0, 5).map((d, i) => (
                    <tr key={i}>
                      <td style={{ padding: '8px 0', borderBottom: '1px solid color-mix(in srgb, var(--border) 50%, transparent)' }}>{d.driver}</td>
                      <td style={{ padding: '8px 0', borderBottom: '1px solid color-mix(in srgb, var(--border) 50%, transparent)', textAlign: 'right', color: d.avg_shap_value > 0 ? 'var(--accent)' : 'inherit' }}>
                        {d.avg_shap_value.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </div>

      {/* Right Panel: Attribution Detail */}
      <div style={{ flex: '1 1 60%', minWidth: '400px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Attribution Detail</h2>
            <div style={{ display: 'flex', gap: '12px' }}>
              <select 
                value={selectedCloud} 
                onChange={(e) => setSelectedCloud(e.target.value)}
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', outline: 'none' }}
              >
                <option value="aws">AWS</option>
                <option value="azure">Azure</option>
                <option value="gcp">GCP</option>
              </select>
              <select 
                value={selectedService} 
                onChange={(e) => setSelectedService(e.target.value)}
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', outline: 'none' }}
              >
                {services.length === 0 && <option value="">No services</option>}
                {services.map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
              </select>
            </div>
          </div>

          {!loadingAttribution && attributionData.length === 0 ? (
            <EmptyState title="No attribution data" message="Select a different service or region" />
          ) : (
            <>
              {trendData.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <h3 style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--text-secondary)' }}>Trend for Selection</h3>
                  <SpendTrendChart data={trendData} loading={loadingAttribution} />
                </div>
              )}
              <h3 style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--text-secondary)' }}>Daily Driver Breakdown</h3>
              <DataTable 
                columns={tableColumns}
                data={attributionData}
                loading={loadingAttribution}
              />
            </>
          )}

        </div>
      </div>

    </div>
  );
};
