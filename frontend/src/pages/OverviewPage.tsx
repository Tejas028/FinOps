import React from 'react';
import { MetricCard } from '../components/shared/MetricCard';
import { SpendTrendChart } from '../components/charts/SpendTrendChart';
import { SpendByCloudChart } from '../components/charts/SpendByCloudChart';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import { useBilling } from '../hooks/useBilling';
import { useAnomalies } from '../hooks/useAnomalies';
import { useForecasts } from '../hooks/useForecasts';
import { useAlerts } from '../hooks/useAlerts';
import { useFilterContext } from '../context/FilterContext';
import { AIInsightPanel } from '../components/shared/AIInsightPanel';

export const OverviewPage: React.FC = () => {
  const { startDate, endDate, cloud } = useFilterContext();
  const { byCloud, trend, loading: loadingBilling } = useBilling();
  const { summary: anomalySummary, recent, loading: loadingAnomalies } = useAnomalies();
  const { latestList, budgetRisk, loading: loadingForecasts } = useForecasts(30);
  const { summary: alertsSummary } = useAlerts();

  // Compute metric sums from data
  let totalSpend = 0;
  if (Array.isArray(byCloud)) {
    totalSpend = byCloud.reduce((sum, item) => sum + item.total_cost_usd, 0);
  }

  let totalForecast = 0;
  if (Array.isArray(latestList) && latestList.length > 0) {
    totalForecast = latestList.reduce((sum, item) => sum + item.predicted_cost, 0);
  }

  const aiPayload = (byCloud && anomalySummary && latestList && alertsSummary) ? {
    date_range_start: startDate,
    date_range_end: endDate,
    total_spend: totalSpend,
    anomaly_count: anomalySummary.total_anomalies,
    critical_count: anomalySummary.by_severity.critical || 0,
    high_count: anomalySummary.by_severity.high || 0,
    forecast_30d: latestList[0]?.predicted_cost || 0,
    by_cloud: Object.fromEntries((byCloud || []).map(c => [c.dimension, c.total_cost_usd])),
    top_anomaly_cloud: Object.entries(anomalySummary.by_cloud || {})
                         .sort((a,b) => (b[1] as number) - (a[1] as number))[0]?.[0] || null,
    unresolved_alerts: alertsSummary.unresolved || 0,
  } : null;

  const aiTrigger = `${startDate}-${endDate}-${cloud}`;

  let budgetRiskColor = 'var(--text-secondary)';
  if (budgetRisk?.breach_risk === 'possible') budgetRiskColor = 'var(--accent-med)';
  if (budgetRisk?.breach_risk === 'likely') budgetRiskColor = 'var(--accent)';
  if (budgetRisk?.breach_risk === 'certain') budgetRiskColor = 'var(--red)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Row 1 - KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
        <MetricCard 
          label={`Total Spend`} 
          value={`$${totalSpend.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          loading={loadingBilling}
        />
        <MetricCard 
          label="Anomalies Detected" 
          value={anomalySummary ? anomalySummary.total_anomalies.toString() : "0"} 
          loading={loadingAnomalies}
        />
        <MetricCard 
          label="Critical Anomalies" 
          value={anomalySummary?.by_severity?.critical?.toString() || "0"} 
          loading={loadingAnomalies}
        />
        <MetricCard 
          label="Forecast (Next 30d)" 
          value={`$${totalForecast.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} 
          loading={loadingForecasts}
        />
      </div>

      {/* AI Daily Summary Card */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Daily Intelligence Summary
          </span>
        </div>
        <AIInsightPanel 
          endpoint="/insights/daily-summary"
          payload={aiPayload}
          trigger={aiTrigger}
          className="overview-ai-insight"
        />
      </div>

      {/* Row 2 - Spend Trends */}
      <div style={{ display: 'grid', gridTemplateColumns: '6fr 4fr', gap: '24px' }}>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Spend Trend</h3>
          <SpendTrendChart data={trend} loading={loadingBilling} />
        </div>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Spend by Cloud</h3>
          {loadingBilling ? <div style={{ height: '120px' }} /> : <SpendByCloudChart data={byCloud} />}
        </div>
      </div>

      {/* Row 3 - Recent Anomalies & Budget Risk */}
      <div style={{ display: 'grid', gridTemplateColumns: '6fr 4fr', gap: '24px' }}>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Recent Anomalies</h3>
          {loadingAnomalies ? (
             <div style={{ height: '150px' }} />
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <tbody>
                {recent.map((a, i) => (
                  <tr key={i} style={{ borderBottom: i < recent.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    <td style={{ padding: '8px 0', color: 'var(--text-secondary)' }}>{a.usage_date}</td>
                    <td style={{ padding: '8px 0', textTransform: 'uppercase' }}>{a.cloud_provider}</td>
                    <td style={{ padding: '8px 0' }}>{a.service}</td>
                    <td style={{ padding: '8px 0' }}><SeverityBadge severity={a.severity} /></td>
                    <td style={{ padding: '8px 0', color: 'var(--red)', textAlign: 'right' }}>+{a.deviation_pct.toFixed(1)}%</td>
                  </tr>
                ))}
                {recent.length === 0 && <tr><td colSpan={5} style={{ padding: '8px 0', color: 'var(--text-secondary)' }}>No recent anomalies.</td></tr>}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px' }}>
           <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Budget Risk</h3>
           {cloud === 'all' ? (
             <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Please select a specific cloud provider to view budget risk.</div>
           ) : !budgetRisk ? (
             <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No active budget set. Go to Forecasts to simulate.</div>
           ) : (
             <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ fontSize: '18px', fontWeight: 600, color: budgetRiskColor, textTransform: 'capitalize' }}>
                  {budgetRisk.breach_risk}
                </div>
                {budgetRisk.breach_date && (
                   <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                     Expected breach by {budgetRisk.breach_date}
                   </div>
                )}
             </div>
           )}
        </div>
      </div>

    </div>
  );
};
