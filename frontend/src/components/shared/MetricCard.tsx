import React from 'react';
import { Skeleton } from './Skeleton';

interface MetricCardProps {
  label: string;
  value: string;
  delta?: number;
  deltaLabel?: string;
  loading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, delta, deltaLabel, loading }) => {
  if (loading) {
    return (
      <div style={{
        padding: '20px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        height: '102px'
      }}>
        <Skeleton height="14px" width="40%" className="mb-2" />
        <Skeleton height="32px" width="70%" />
      </div>
    );
  }

  const isPositive = delta !== undefined && delta > 0;
  const isNegative = delta !== undefined && delta < 0;
  
  // In FinOps, cost decrease (negative) is good/green, increase is bad/red.
  const deltaColor = isPositive ? 'var(--red)' : isNegative ? 'var(--green)' : 'var(--text-secondary)';
  const arrow = isPositive ? '↑' : isNegative ? '↓' : '';
  const formattedDelta = delta !== undefined ? Math.abs(delta).toFixed(1) + '%' : null;

  return (
    <div style={{
      padding: '20px',
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <div style={{
        fontSize: '12px',
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {label}
      </div>
      
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
        <div style={{
          fontSize: '28px',
          fontVariantNumeric: 'tabular-nums',
          color: 'var(--text-primary)',
          fontWeight: 600
        }}>
          {value}
        </div>
        
        {delta !== undefined && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: deltaColor }}>
              {arrow} {formattedDelta}
            </span>
            {deltaLabel && (
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                {deltaLabel}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
