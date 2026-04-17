import React, { useState, useEffect, useMemo } from 'react';
import { useForecasts } from '../hooks/useForecasts';
import { useFilterContext } from '../context/FilterContext';
import { ForecastChart } from '../components/charts/ForecastChart';
import { DataTable, ColumnDef } from '../components/shared/DataTable';
import { apiFetch } from '../api/client';
import type { ForecastItem, SpendByDimension } from '../types';

export const ForecastPage: React.FC = () => {
  const { cloud, startDate, endDate } = useFilterContext();
  const [horizonDays, setHorizonDays] = useState<number>(30);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  
  // Section A Data (Aggregated Cloud)
  const { latestList: aggregateForecasts, loading: loadingAggregate } = useForecasts(horizonDays);
  
  // Default bounds for budget risk based on cloud
  const defaultBudget = useMemo(() => {
    if (cloud === 'aws') return 180000;
    if (cloud === 'azure') return 160000;
    if (cloud === 'gcp') return 140000;
    return 50000;
  }, [cloud]);

  const [budget, setBudget] = useState<number>(defaultBudget);
  const [debouncedBudget, setDebouncedBudget] = useState(defaultBudget);

  // Sync budget when cloud changes
  useEffect(() => {
    setBudget(defaultBudget);
    setDebouncedBudget(defaultBudget);
  }, [defaultBudget]);

  const { budgetRisk, fetchBudgetRisk } = useForecasts(horizonDays);

  // Debounce budget input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedBudget(budget), 500);
    return () => clearTimeout(t);
  }, [budget]);

  // Fetch on debounced budget or cloud change
  useEffect(() => {
    if (debouncedBudget > 0) {
      fetchBudgetRisk(debouncedBudget);
    }
  }, [debouncedBudget, cloud, fetchBudgetRisk]);

  // Section B Data (Per-Service Drill-down)
  const [services, setServices] = useState<string[]>([]);
  const [selectedService, setSelectedService] = useState<string>('');
  
  // Fetch services for dropdown
  useEffect(() => {
    let active = true;
    const fetchServices = async () => {
      try {
        const params: any = { start_date: startDate, end_date: endDate, top_n: 50 };
        if (cloud !== 'all') params.cloud_provider = cloud;
        const data = await apiFetch<SpendByDimension[]>('/billing/by-service', params);
        if (active) {
          const serviceNames = data.map(d => d.dimension);
          setServices(serviceNames);
          if (serviceNames.length && !serviceNames.includes(selectedService)) {
            setSelectedService(serviceNames[0]);
          } else if (serviceNames.length === 0) {
            setSelectedService('');
          }
        }
      } catch (err) {
        console.error("Failed to load services:", err);
      }
    };
    if (startDate && endDate) {
      fetchServices();
    }
    return () => { active = false; };
  }, [cloud, startDate, endDate]);

  const { latestList: serviceForecasts, forecastsPage, loading: loadingService, fetchForecasts } = useForecasts(horizonDays, selectedService || undefined);

  // Sync pagination
  useEffect(() => {
    fetchForecasts(page, pageSize);
  }, [page, pageSize, fetchForecasts]);

  // Reset page
  useEffect(() => {
    setPage(1);
  }, [horizonDays, selectedService, pageSize]);

  const horizonOptions = [7, 14, 30, 90];

  const columns: ColumnDef<ForecastItem>[] = [
    { key: "date", header: "Forecast Date", render: (f) => f.forecast_date },
    { key: "predicted", header: "Predicted Cost", render: (f) => `$${f.predicted_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "lower", header: "Lower Bound", render: (f) => `$${f.lower_bound.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "upper", header: "Upper Bound", render: (f) => `$${f.upper_bound.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "model", header: "Model", render: (f) => f.model_used },
    { key: "confidence", header: "Confidence Band Width", render: (f) => `$${(f.upper_bound - f.lower_bound).toLocaleString(undefined, { maximumFractionDigits: 2 })}` }
  ];

  let budgetRiskColor = 'var(--text-secondary)';
  if (budgetRisk?.breach_risk === 'possible') budgetRiskColor = 'var(--accent-dim)';
  if (budgetRisk?.breach_risk === 'likely') budgetRiskColor = 'var(--accent-med)';
  if (budgetRisk?.breach_risk === 'certain') budgetRiskColor = 'var(--accent)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top: Horizon Selector */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-secondary)', marginRight: "8px" }}>Forecast Horizon:</span>
        {horizonOptions.map((days) => {
          const isActive = horizonDays === days;
          return (
            <button
              key={days}
              onClick={() => setHorizonDays(days)}
              style={{
                background: isActive ? 'var(--accent-dim)' : 'transparent',
                border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                padding: '6px 16px',
                borderRadius: '16px',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              {days}d
            </button>
          );
        })}
      </div>

      {/* Row 1: Section A - Aggregated Forecast & Budget Risk */}
      <div style={{ display: 'grid', gridTemplateColumns: '7fr 3fr', gap: '24px' }}>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600, textTransform: 'capitalize' }}>
            {cloud === 'all' ? 'Multi-Cloud Aggregated Forecast' : `${cloud} Aggregated Forecast`}
          </h3>
          <ForecastChart data={aggregateForecasts} horizonDays={horizonDays} loading={loadingAggregate} />
        </div>

        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600 }}>Budget Risk Assessment</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Monthly Budget (USD)
              </label>
              <input 
                type="number" 
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                placeholder="e.g. 50000"
                style={{
                  width: '100%',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              {cloud === 'all' && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Select a specific cloud provider to simulate budget accurately.
                </div>
              )}
            </div>

            {budgetRisk && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ 
                  fontSize: '18px', 
                  fontWeight: 600, 
                  color: budgetRisk.breach_risk === 'certain' ? 'var(--bg-base)' : budgetRiskColor,
                  background: budgetRisk.breach_risk === 'certain' ? 'var(--accent-full)' : budgetRisk.breach_risk === 'likely' ? 'var(--accent-med)' : 'transparent',
                  padding: budgetRisk.breach_risk === 'certain' || budgetRisk.breach_risk === 'likely' ? '4px 12px' : 0,
                  borderRadius: '16px',
                  display: 'inline-flex',
                  alignSelf: 'flex-start'
                }}>
                  {budgetRisk.breach_risk === 'none' && "No breach expected"}
                  {budgetRisk.breach_risk === 'possible' && "Breach Possible"}
                  {budgetRisk.breach_risk === 'likely' && "Breach Likely"}
                  {budgetRisk.breach_risk === 'certain' && `Breach Expected in ${budgetRisk.days_to_breach} days`}
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '12px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Projected Monthly Cost:</span>
                  <span style={{ fontWeight: 600 }}>${budgetRisk.projected_monthly_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Budget Threshold:</span>
                  <span>${budgetRisk.monthly_budget_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Section B - Per-Service Drill-down */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Per-Service Drill-down</h3>
          <select 
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '13px',
              outline: 'none',
              minWidth: '200px'
            }}
          >
            {services.length === 0 && <option value="">No services available</option>}
            {services.map(svc => (
              <option key={svc} value={svc}>{svc}</option>
            ))}
          </select>
        </div>
        
        {selectedService ? (
           <ForecastChart data={serviceForecasts} horizonDays={horizonDays} loading={loadingService} />
        ) : (
           <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
              Select a service to view its forecast
           </div>
        )}
      </div>

      {/* Row 3: Forecast Data Table */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600 }}>Forecast Data Points {selectedService && `(${selectedService})`}</h3>
        </div>
        <DataTable 
          columns={columns}
          data={forecastsPage?.data || []}
          total={forecastsPage?.total || 0}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          loading={loadingService}
        />
      </div>

    </div>
  );
};
