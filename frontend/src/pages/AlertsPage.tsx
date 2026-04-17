import React, { useState, useEffect, useCallback } from 'react';
import { useFilterContext } from '../context/FilterContext';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import { getAlerts, getAlertsSummary, resolveAlert } from '../api/alerts';
import type { AlertListItem, AlertSummary, PaginatedResponse } from '../types';
import { Bell, CheckCircle, ChevronDown, ChevronRight } from 'lucide-react';

const selectStyle: React.CSSProperties = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border)',
  color: 'var(--text-primary)',
  padding: '6px 12px',
  borderRadius: '6px',
  fontSize: '13px',
  outline: 'none',
};

export const AlertsPage: React.FC = () => {
  const { startDate, endDate, cloud } = useFilterContext();

  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [alertsData, setAlertsData] = useState<PaginatedResponse<AlertListItem> | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [cloudFilter, setCloudFilter] = useState('');
  const [resolvedFilter, setResolvedFilter] = useState<'' | 'false' | 'true'>('false');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const fetchSummary = useCallback(async () => {
    try {
      const data = await getAlertsSummary({ start_date: startDate, end_date: endDate });
      setSummary(data);
    } catch (e) {
      console.error('Failed to fetch alerts summary', e);
    }
  }, [startDate, endDate]);

  const fetchAlerts = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean | undefined> = {
        start_date: startDate,
        end_date: endDate,
        page: p,
        page_size: PAGE_SIZE,
      };
      if (severityFilter) params.severity = severityFilter;
      if (typeFilter) params.alert_type = typeFilter;
      const effectiveCloud = cloudFilter || (cloud !== 'all' ? cloud : '');
      if (effectiveCloud) params.cloud_provider = effectiveCloud;
      if (resolvedFilter !== '') params.is_resolved = resolvedFilter === 'true';

      // @ts-ignore
      const data = await getAlerts(params);
      setAlertsData(data);
      setPage(p);
    } catch (e) {
      console.error('Failed to fetch alerts', e);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, severityFilter, typeFilter, cloudFilter, cloud, resolvedFilter]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    fetchAlerts(1);
  }, [fetchAlerts]);

  const handleResolve = async (alertId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setResolvingId(alertId);
    try {
      await resolveAlert(alertId);
      await Promise.all([fetchAlerts(page), fetchSummary()]);
    } catch (err) {
      console.error('Failed to resolve alert', err);
    } finally {
      setResolvingId(null);
    }
  };

  const toggleExpand = (alertId: string) => {
    setExpandedId(prev => (prev === alertId ? null : alertId));
  };

  const typeLabels: Record<string, string> = {
    anomaly_detected: 'Anomaly',
    spend_spike: 'Spend Spike',
    budget_breach_imminent: 'Budget Breach',
    forecast_exceeded: 'Forecast Exceeded',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Summary Bar */}
      {summary && (
        <div style={{
          display: 'flex', gap: '40px', paddingBottom: '20px',
          borderBottom: '1px solid var(--border)', alignItems: 'flex-end'
        }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Total Alerts</div>
            <div style={{ fontSize: '24px', fontWeight: 700 }}>{summary.total}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Unresolved</div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent)' }}>{summary.unresolved}</div>
          </div>
          <div style={{ display: 'flex', gap: '24px', marginLeft: '8px' }}>
            {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
              <div key={sev}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>{sev}</div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: sev === 'critical' ? 'var(--accent-full)' : 'var(--text-primary)' }}>
                  {summary.by_severity[sev] || 0}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} style={selectStyle}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={selectStyle}>
          <option value="">All Types</option>
          <option value="anomaly_detected">Anomaly Detected</option>
          <option value="spend_spike">Spend Spike</option>
          <option value="budget_breach_imminent">Budget Breach</option>
        </select>
        <select value={cloudFilter} onChange={e => setCloudFilter(e.target.value)} style={selectStyle}>
          <option value="">All Clouds</option>
          <option value="aws">AWS</option>
          <option value="azure">Azure</option>
          <option value="gcp">GCP</option>
        </select>
        <select value={resolvedFilter} onChange={e => setResolvedFilter(e.target.value as '' | 'true' | 'false')} style={selectStyle}>
          <option value="false">Unresolved Only</option>
          <option value="true">Resolved Only</option>
          <option value="">All</option>
        </select>
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
          {alertsData ? `${alertsData.total} result${alertsData.total !== 1 ? 's' : ''}` : ''}
        </span>
      </div>

      {/* Alerts Table */}
      <div style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border)',
        borderRadius: '8px', overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '110px 70px 130px 90px 1fr 110px 100px',
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
          letterSpacing: '0.5px', color: 'var(--text-secondary)'
        }}>
          <span>Date</span>
          <span>Cloud</span>
          <span>Type</span>
          <span>Severity</span>
          <span>Title</span>
          <span>Status</span>
          <span></span>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading alerts…
          </div>
        ) : (alertsData?.data.length ?? 0) === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Bell size={32} style={{ opacity: 0.3, display: 'block', margin: '0 auto 12px' }} />
            No alerts found for the current filters.
          </div>
        ) : (
          alertsData!.data.map((alert, i) => {
            const isExpanded = expandedId === alert.alert_id;
            const isResolving = resolvingId === alert.alert_id;
            const isLast = i === alertsData!.data.length - 1;

            return (
              <div key={alert.alert_id}>
                {/* Row */}
                <div
                  onClick={() => toggleExpand(alert.alert_id)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '110px 70px 130px 90px 1fr 110px 100px',
                    padding: '12px 16px',
                    borderBottom: isLast && !isExpanded ? 'none' : '1px solid var(--border)',
                    cursor: 'pointer',
                    fontSize: '13px',
                    alignItems: 'center',
                    background: isExpanded ? 'var(--bg-elevated)' : 'transparent',
                    transition: 'background 0.15s ease',
                    opacity: alert.is_resolved ? 0.5 : 1,
                  }}
                  onMouseEnter={e => {
                    if (!isExpanded) (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-elevated)';
                  }}
                  onMouseLeave={e => {
                    if (!isExpanded) (e.currentTarget as HTMLDivElement).style.background = 'transparent';
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{alert.alert_date}</span>
                  <span style={{ textTransform: 'uppercase', fontWeight: 500, fontSize: '12px' }}>{alert.cloud_provider}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                    {typeLabels[alert.alert_type] || alert.alert_type}
                  </span>
                  <SeverityBadge severity={alert.severity} />
                  <span style={{
                    fontWeight: 500,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    paddingRight: '8px'
                  }}>
                    {alert.title}
                  </span>
                  <span>
                    {alert.is_resolved ? (
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={12} /> Resolved
                      </span>
                    ) : (
                      <SeverityBadge severity={alert.severity} />
                    )}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
                    {!alert.is_resolved && (
                      <button
                        onClick={(e) => handleResolve(alert.alert_id, e)}
                        disabled={isResolving}
                        style={{
                          background: 'transparent',
                          border: '1px solid var(--accent-med)',
                          color: 'var(--accent)',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          cursor: 'pointer',
                          opacity: isResolving ? 0.5 : 1,
                          transition: 'all 0.15s',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {isResolving ? '…' : 'Resolve'}
                      </button>
                    )}
                    {isExpanded
                      ? <ChevronDown size={14} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                      : <ChevronRight size={14} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                    }
                  </div>
                </div>

                {/* Accordion expansion */}
                {isExpanded && (
                  <div style={{
                    padding: '12px 16px 16px 16px',
                    background: 'var(--bg-elevated)',
                    borderBottom: isLast ? 'none' : '1px solid var(--border)',
                    borderTop: '1px solid var(--border)',
                  }}>
                    <p style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                      {alert.message}
                    </p>
                    <div style={{ display: 'flex', gap: '24px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                      {alert.service_category && <span>Service: <strong style={{ color: 'var(--text-primary)' }}>{alert.service_category}</strong></span>}
                      <span>Created: <strong style={{ color: 'var(--text-primary)' }}>{alert.created_at?.slice(0, 10)}</strong></span>
                      <span>Alert ID: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '11px' }}>{alert.alert_id}</strong></span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {alertsData && alertsData.total > PAGE_SIZE && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button
            onClick={() => fetchAlerts(page - 1)}
            disabled={page <= 1}
            style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              color: 'var(--text-secondary)', padding: '6px 14px', borderRadius: '6px',
              cursor: page <= 1 ? 'not-allowed' : 'pointer', fontSize: '13px',
              opacity: page <= 1 ? 0.4 : 1
            }}
          >
            Previous
          </button>
          <span style={{ padding: '6px 12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Page {page} of {Math.ceil(alertsData.total / PAGE_SIZE)}
          </span>
          <button
            onClick={() => fetchAlerts(page + 1)}
            disabled={!alertsData.has_next}
            style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              color: 'var(--text-secondary)', padding: '6px 14px', borderRadius: '6px',
              cursor: !alertsData.has_next ? 'not-allowed' : 'pointer', fontSize: '13px',
              opacity: !alertsData.has_next ? 0.4 : 1
            }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
