import React, { useState } from 'react';
import { useAnomalies } from '../hooks/useAnomalies';
import { DataTable, ColumnDef } from '../components/shared/DataTable';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import { AnomalyDrawer } from '../components/anomalies/AnomalyDrawer';
import type { AnomalyListItem } from '../types';

export const AnomaliesPage: React.FC = () => {
  const [severityFilter, setSeverityFilter] = useState("all");
  const { anomalies, summary, loading, fetchAnomalies } = useAnomalies(severityFilter);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | null>(null);

  const columns: ColumnDef<AnomalyListItem>[] = [
    { key: "date", header: "Date", render: (a) => a.usage_date },
    { key: "cloud", header: "Cloud", render: (a) => <span style={{ textTransform: 'uppercase' }}>{a.cloud_provider}</span> },
    { key: "service", header: "Service", render: (a) => a.service },
    { key: "severity", header: "Severity", render: (a) => <SeverityBadge severity={a.severity} /> },
    { key: "actual", header: "Actual Cost", render: (a) => `$${a.actual_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "expected", header: "Expected Cost", render: (a) => `$${a.expected_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "deviation", header: "Deviation %", render: (a) => <span style={{ color: 'var(--red)' }}>+{a.deviation_pct.toFixed(1)}%</span> },
    { key: "method", header: "Method", render: (a) => a.detection_method }
  ];

  const handlePageChange = (newPage: number) => {
    fetchAnomalies(newPage);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Stats */}
      {summary && (
        <div style={{ display: 'flex', gap: '32px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginRight: '8px' }}>Total Anomalies:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.total_anomalies}</span>
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginRight: '8px' }}>Critical:</span>
            <span style={{ fontSize: '18px', fontWeight: 600, color: 'var(--accent)' }}>{summary.by_severity.critical || 0}</span>
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginRight: '8px' }}>High:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.by_severity.high || 0}</span>
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginRight: '8px' }}>Medium:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.by_severity.medium || 0}</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Filter by Severity:</span>
        <select 
          value={severityFilter} 
          onChange={(e) => setSeverityFilter(e.target.value)}
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            outline: 'none',
          }}
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Main Table */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px' }}>
        <DataTable 
          columns={columns}
          data={anomalies?.data || []}
          total={anomalies?.total || 0}
          page={anomalies?.page || 1}
          pageSize={anomalies?.page_size || 20}
          onPageChange={handlePageChange}
          loading={loading}
          onRowClick={(item) => setSelectedAnomalyId(item.anomaly_id)}
        />
      </div>

      <AnomalyDrawer 
        anomalyId={selectedAnomalyId} 
        onClose={() => setSelectedAnomalyId(null)} 
      />
    </div>
  );
};
