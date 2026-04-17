import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { TrendPoint } from '../../types';
import { Skeleton } from '../shared/Skeleton';

interface SpendTrendChartProps {
  data: TrendPoint[];
  loading?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        padding: '8px 12px',
        borderRadius: '6px',
        color: 'var(--text-primary)',
        fontSize: '12px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <p style={{ margin: '0 0 4px 0', color: 'var(--text-secondary)' }}>{label}</p>
        <p style={{ margin: 0, fontWeight: 600, color: 'var(--accent)' }}>
          ${payload[0].value.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

export const SpendTrendChart: React.FC<SpendTrendChartProps> = ({ data, loading }) => {
  if (loading && data.length === 0) {
    return <Skeleton height="200px" />;
  }

  const formatYAxis = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}m`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  return (
    <div style={{ width: '100%', height: '200px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} vertical={false} />
          <XAxis 
            dataKey="period" 
            stroke="var(--text-secondary)" 
            fontSize={11} 
            tickLine={false}
            axisLine={false}
            minTickGap={30}
          />
          <YAxis 
            stroke="var(--text-secondary)" 
            fontSize={11} 
            tickLine={false}
            axisLine={false}
            tickFormatter={formatYAxis}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="total_cost_usd" 
            stroke="var(--accent)" 
            strokeWidth={1.5}
            fillOpacity={1} 
            fill="url(#colorSpend)" 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
