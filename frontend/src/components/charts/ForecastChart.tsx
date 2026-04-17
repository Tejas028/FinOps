import React from 'react';
import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ForecastItem } from '../../types';
import { Skeleton } from '../shared/Skeleton';

interface ForecastChartProps {
  data: ForecastItem[];
  horizonDays: number;
  loading?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as ForecastItem;
    return (
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        padding: '8px 12px',
        borderRadius: '6px',
        color: 'var(--text-primary)',
        fontSize: '12px'
      }}>
        <p style={{ margin: '0 0 6px 0', color: 'var(--text-secondary)' }}>{label}</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
            <span style={{ color: 'var(--accent)' }}>Predicted:</span>
            <span style={{ fontWeight: 600 }}>${data.predicted_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', color: 'var(--text-secondary)' }}>
            <span>Range:</span>
            <span>
              ${data.lower_bound.toLocaleString(undefined, { maximumFractionDigits: 0 })} 
              {" - "} 
              ${data.upper_bound.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const ForecastChart: React.FC<ForecastChartProps> = ({ data, horizonDays: _horizonDays, loading }) => {
  if (loading && data.length === 0) {
     return <Skeleton height="220px" />;
  }

  const formatYAxis = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}m`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  const chartData = data.map(d => ({
    ...d,
    confidenceBand: [d.lower_bound, d.upper_bound]
  })).sort((a, b) => new Date(a.forecast_date).getTime() - new Date(b.forecast_date).getTime());

  return (
    <div style={{ width: '100%', height: '220px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} vertical={false} />
          <XAxis 
            dataKey="forecast_date" 
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
            dataKey="confidenceBand" 
            stroke="none" 
            fill="var(--accent-dim)" 
            fillOpacity={1}
            isAnimationActive={false}
          />
          <Line 
            type="monotone" 
            dataKey="predicted_cost" 
            stroke="var(--accent)" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: 'var(--bg-base)', stroke: 'var(--accent)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
