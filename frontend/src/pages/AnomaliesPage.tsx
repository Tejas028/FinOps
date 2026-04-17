import React, { useState, useEffect, useRef } from 'react';
import { useAnomalies } from '../hooks/useAnomalies';
import { DataTable, ColumnDef } from '../components/shared/DataTable';
import { SeverityBadge } from '../components/shared/SeverityBadge';
import { AnomalyDrawer } from '../components/anomalies/AnomalyDrawer';
import { AIInsightPanel } from '../components/shared/AIInsightPanel';
import { ChevronRight } from 'lucide-react';
import { ExportButton } from '../components/shared/ExportButton';
import { exportToCsv } from '../utils/exportCsv';
import type { AnomalyListItem } from '../types';

export const AnomaliesPage: React.FC = () => {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { anomalies, summary, loading, fetchAnomalies } = useAnomalies(severityFilter);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | null>(null);
  const [expandedAnomalyId, setExpandedAnomalyId] = useState<string | null>(null);
  const tableContainerRef = useRef<HTMLDivElement>(null);

  // Sync data on page or size change
  useEffect(() => {
    fetchAnomalies(page, pageSize);
  }, [page, pageSize, fetchAnomalies]);

  // Reset to page 1 when filters or size change
  useEffect(() => {
    setPage(1);
  }, [severityFilter, pageSize]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    tableContainerRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const columns: ColumnDef<AnomalyListItem>[] = [
    { key: "date", header: "Date", render: (a) => a.usage_date },
    { key: "cloud", header: "Cloud", render: (a) => <span style={{ textTransform: 'uppercase' }}>{a.cloud_provider}</span> },
    { key: "service", header: "Service", render: (a) => a.service },
    { key: "severity", header: "Severity", render: (a) => <SeverityBadge severity={a.severity} /> },
    { key: "actual", header: "Actual Cost", render: (a) => `$${a.actual_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "expected", header: "Expected Cost", render: (a) => `$${a.expected_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}` },
    { key: "deviation", header: "Deviation %", render: (a) => <span style={{ color: 'var(--accent)' }}>+{a.deviation_pct.toFixed(1)}%</span> },
    { key: "method", header: "Method", render: (a) => a.detection_method },
    { 
      key: "actions", 
      header: "", 
      render: (a) => (
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'flex-end' }}>
          <button 
            onClick={(e) => { e.stopPropagation(); setSelectedAnomalyId(a.anomaly_id); }}
            style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '11px', textTransform: 'uppercase' }}
          >
            Details
          </button>
          <ChevronRight 
            size={16} 
            style={{ 
              transform: expandedAnomalyId === a.anomaly_id ? 'rotate(90deg)' : 'none',
              transition: 'transform 0.2s ease',
              color: 'var(--text-secondary)'
            }} 
          />
        </div>
      ) 
    }
  ];

  const renderAIInsight = (a: AnomalyListItem) => (
    <AIInsightPanel 
      endpoint="/insights/anomaly"
      payload={{
        cloud_provider: a.cloud_provider,
        service: a.service,
        date: a.usage_date,
        actual_cost: a.actual_cost,
        expected_cost: a.expected_cost,
        deviation_pct: a.deviation_pct,
        severity: a.severity,
        detection_method: a.detection_method,
        z_score: (a as any).z_score || null
      }}
      trigger={expandedAnomalyId || ''}
    />
  );

  const handleRowClick = (item: AnomalyListItem) => {
    setExpandedAnomalyId(prev => prev === item.anomaly_id ? null : item.anomaly_id);
  };

  const handleExport = () => {
    if (!anomalies) return;
    const exportData = anomalies.data.map(a => ({
      usage_date: a.usage_date,
      cloud_provider: a.cloud_provider,
      service: a.service,
      severity: a.severity,
      actual_cost: a.actual_cost,
      expected_cost: a.expected_cost,
      deviation_pct: a.deviation_pct,
      detection_method: a.detection_method,
      anomaly_id: a.anomaly_id
    }));
    exportToCsv("anomalies.csv", exportData);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Stats */}
      {summary && (
        <div style={{ display: 'flex', gap: '32px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginRight: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Anomalies:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.total_anomalies}</span>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginRight: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Critical:</span>
            <span style={{ fontSize: '18px', fontWeight: 600, color: '#F59E0B' }}>{summary.by_severity.critical || 0}</span>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginRight: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>High:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.by_severity.high || 0}</span>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginRight: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Medium:</span>
            <span style={{ fontSize: '18px', fontWeight: 600 }}>{summary.by_severity.medium || 0}</span>
          </div>
        </div>
      )}

      {/* Actions and Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
        <ExportButton 
          onClick={handleExport} 
          disabled={!anomalies || anomalies.data.length === 0} 
        />
      </div>

      {/* Main Table */}
      <div 
        ref={tableContainerRef}
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '8px' }}
      >
        <DataTable 
          columns={columns}
          data={anomalies?.data || []}
          total={anomalies?.total || 0}
          page={page}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={setPageSize}
          loading={loading}
          onRowClick={handleRowClick}
          renderExpandedRow={renderAIInsight}
          expandedRowId={expandedAnomalyId}
          getRowId={(a) => a.anomaly_id}
        />
      </div>

      <AnomalyDrawer 
        anomalyId={selectedAnomalyId} 
        onClose={() => setSelectedAnomalyId(null)} 
      />
    </div>
  );
};
