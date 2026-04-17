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
}

export function DataTable<T>({
  columns,
  data,
  total = 0,
  page = 1,
  pageSize = 20,
  onPageChange,
  loading,
  onRowClick
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
          {data.map((item, idx) => (
            <tr 
              key={idx} 
              onClick={() => onRowClick?.(item)}
              style={{
                borderBottom: '1px solid color-mix(in srgb, var(--border) 50%, transparent)',
                cursor: onRowClick ? 'pointer' : 'default',
                transition: 'background 0.2s ease',
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
          ))}
        </tbody>
      </table>

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
