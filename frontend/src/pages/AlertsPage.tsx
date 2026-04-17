import React, { useState, useEffect, useCallback } from 'react';
import { useFilterContext } from '../context/FilterContext';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import { DataTable, ColumnDef } from '../components/shared/DataTable';
import { ExportButton } from '../components/shared/ExportButton';
import { exportToCsv } from '../utils/exportCsv';
import { getAlerts, getAlertsSummary, resolveAlert } from '../api/alerts';
import type { AlertListItem, AlertSummary, PaginatedResponse } from '../types';
import { CheckCircle, ChevronRight, ChevronDown } from 'lucide-react';

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
  const [pageSize, setPageSize] = useState(25);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await getAlertsSummary({ start_date: startDate, end_date: endDate });
      setSummary(data);
    } catch (e) {
      console.error('Failed to fetch alerts summary', e);
    }
  }, [startDate, endDate]);

  const fetchAlerts = useCallback(async (p = 1, pSize = 25) => {
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean | undefined> = {
        start_date: startDate,
        end_date: endDate,
        page: p,
        page_size: pSize,
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
    setPage(1);
    fetchAlerts(1, pageSize);
  }, [fetchAlerts, pageSize]);

  const handlePageChange = (newPage: number) => {
    fetchAlerts(newPage, pageSize);
  };

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

  const typeLabels: Record<string, string> = {
    anomaly_detected: 'Anomaly',
    spend_spike: 'Spend Spike',
    budget_breach_imminent: 'Budget Breach',
    forecast_exceeded: 'Forecast Exceeded',
  };

  const columns: ColumnDef<AlertListItem>[] = [
    { key: "date", header: "Date", render: (a) => <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{a.alert_date}</span> },
    { key: "cloud", header: "Cloud", render: (a) => <span style={{ textTransform: 'uppercase', fontWeight: 500, fontSize: '12px' }}>{a.cloud_provider}</span> },
    { key: "type", header: "Type", render: (a) => <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{typeLabels[a.alert_type] || a.alert_type}</span> },
    { key: "severity", header: "Severity", render: (a) => <SeverityBadge severity={a.severity} /> },
    { key: "title", header: "Title", render: (a) => <span style={{ fontWeight: 500 }}>{a.title}</span> },
    { 
      key: "status", 
      header: "Status", 
      render: (a) => a.is_resolved ? (
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CheckCircle size={12} /> Resolved
        </span>
      ) : (
        <SeverityBadge severity={a.severity} />
      )
    },
    {
      key: "actions",
      header: "",
      render: (a) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
          {!a.is_resolved && (
            <button
              onClick={(e) => handleResolve(a.alert_id, e)}
              disabled={resolvingId === a.alert_id}
              style={{
                background: 'transparent',
                border: '1px solid var(--accent-med)',
                color: 'var(--accent)',
                padding: '3px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                cursor: 'pointer',
                opacity: resolvingId === a.alert_id ? 0.5 : 1,
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              {resolvingId === a.alert_id ? '…' : 'Resolve'}
            </button>
          )}
          {expandedId === a.alert_id
            ? <ChevronDown size={14} style={{ color: 'var(--text-secondary)' }} />
            : <ChevronRight size={14} style={{ color: 'var(--text-secondary)' }} />
          }
        </div>
      )
    }
  ];

  const handleExport = () => {
    if (!alertsData) return;
    const exportData = alertsData.data.map(a => ({
      alert_date: a.alert_date,
      cloud_provider: a.cloud_provider,
      alert_type: a.alert_type,
      severity: a.severity,
      title: a.title,
      message: a.message,
      is_resolved: a.is_resolved,
      created_at: a.created_at
    }));
    exportToCsv("alerts.csv", exportData);
  };

  const renderExpandedRow = (a: AlertListItem) => (
    <div style={{ padding: '8px 0' }}>
      <p style={{ margin: '0 0 12px', fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.6 }}>
        {a.message}
      </p>
      <div style={{ display: 'flex', gap: '24px', fontSize: '12px', color: 'var(--text-secondary)' }}>
        {a.service_category && <span>Service: <strong style={{ color: 'var(--text-primary)' }}>{a.service_category}</strong></span>}
        <span>Created: <strong style={{ color: 'var(--text-primary)' }}>{a.created_at?.slice(0, 10)}</strong></span>
        <span>Alert ID: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '11px' }}>{a.alert_id}</strong></span>
      </div>
    </div>
  );

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
        </div>
        <ExportButton onClick={handleExport} disabled={!alertsData || alertsData.data.length === 0} />
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px' }}>
        <DataTable 
          columns={columns}
          data={alertsData?.data || []}
          total={alertsData?.total || 0}
          page={page}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={setPageSize}
          loading={loading}
          getRowId={(a) => a.alert_id}
          onRowClick={(a) => setExpandedId(prev => prev === a.alert_id ? null : a.alert_id)}
          expandedRowId={expandedId}
          renderExpandedRow={renderExpandedRow}
        />
      </div>
    </div>
  );
};
