import React from 'react';
import { Skeleton } from './Skeleton';
import { EmptyState } from './EmptyState';

export interface ColumnDef<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  total?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  loading?: boolean;
  onRowClick?: (item: T) => void;
  renderExpandedRow?: (item: T) => React.ReactNode;
  expandedRowId?: string | number | null;
  getRowId?: (item: T) => string | number;
}

export function DataTable<T>({
  columns,
  data,
  total = 0,
  page = 1,
  pageSize = 20,
  onPageChange,
  loading,
  onRowClick,
  renderExpandedRow,
  expandedRowId,
  getRowId
}: DataTableProps<T>) {

  if (loading && data.length === 0) {
    return (
      <div style={{ padding: '24px', background: 'var(--bg-surface)' }}>
        <Skeleton height="32px" className="mb-4" />
        <Skeleton height="32px" className="mb-4" />
        <Skeleton height="32px" />
      </div>
    );
  }

  if (!loading && data.length === 0) {
    return <EmptyState />;
  }

  const hasNext = (page * pageSize) < total;
  const hasPrev = page > 1;

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={{
                padding: '12px 16px',
                borderBottom: '1px solid var(--border)',
                fontSize: '11px',
                textTransform: 'uppercase',
                color: 'var(--text-secondary)',
                fontWeight: 500
              }}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => {
            const isExpanded = getRowId && expandedRowId === getRowId(item);
            
            return (
              <React.Fragment key={getRowId ? getRowId(item) : idx}>
                <tr 
                  onClick={() => onRowClick?.(item)}
                  style={{
                    borderBottom: isExpanded ? 'none' : '1px solid color-mix(in srgb, var(--border) 50%, transparent)',
                    cursor: onRowClick ? 'pointer' : 'default',
                    transition: 'background 0.2s ease',
                    borderLeft: isExpanded ? '2px solid #F59E0B' : '2px solid transparent',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-elevated)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  {columns.map((col) => (
                    <td key={col.key} style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text-primary)' }}>
                      {col.render(item)}
                    </td>
                  ))}
                </tr>
                {isExpanded && renderExpandedRow && (
                  <tr>
                    <td colSpan={columns.length} style={{
                      padding: '12px 16px 12px 48px',
                      background: '#0F0F16',
                      borderBottom: '1px solid var(--border)',
                      borderLeft: '2px solid #F59E0B',
                    }}>
                      <div style={{ animation: 'slideIn 0.2s ease' }}>
                        {renderExpandedRow(item)}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {onPageChange && (total > pageSize) && (
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          padding: '16px',
          gap: '16px',
          fontSize: '13px',
          color: 'var(--text-secondary)'
        }}>
          <span>Page {page} of {Math.ceil(total / pageSize)} ({total} total)</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              disabled={!hasPrev}
              onClick={() => hasPrev && onPageChange(page - 1)}
              style={{
                background: 'transparent', border: 'none', color: hasPrev ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: hasPrev ? 'pointer' : 'not-allowed'
              }}
            >
              Prev
            </button>
            <button
              disabled={!hasNext}
              onClick={() => hasNext && onPageChange(page + 1)}
              style={{
                background: 'transparent', border: 'none', color: hasNext ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: hasNext ? 'pointer' : 'not-allowed'
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
