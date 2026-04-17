import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { SpendByDimension } from '../../types';

interface SpendByCloudChartProps {
  data: SpendByDimension[];
}

const CLOUD_COLORS: Record<string, string> = {
  aws: '#F59E0B',    // 100% amber
  azure: '#D97706',  // Medium amber
  gcp: '#92400E',    // Darkest amber
  other: '#7B7B96'
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        padding: '8px 12px',
        borderRadius: '6px',
        color: 'var(--text-primary)',
        fontSize: '12px',
      }}>
        <p style={{ margin: '0 0 4px 0', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
          {data.dimension}
        </p>
        <p style={{ margin: 0, fontWeight: 600 }}>
          ${data.total_cost_usd.toLocaleString()} <span style={{ opacity: 0.7, fontWeight: 400 }}>({data.pct_of_total.toFixed(1)}%)</span>
        </p>
      </div>
    );
  }
  return null;
};

export const SpendByCloudChart: React.FC<SpendByCloudChartProps> = ({ data }) => {
  return (
    <div style={{ width: '100%', height: '120px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          data={data} 
          layout="vertical" 
          margin={{ top: 0, right: 40, left: 0, bottom: 0 }}
        >
          <XAxis type="number" hide />
          <YAxis 
            type="category" 
            dataKey="dimension" 
            stroke="var(--text-secondary)" 
            fontSize={11} 
            tickLine={false}
            axisLine={false}
            width={50}
            style={{ textTransform: 'uppercase' }}
          />
          <Tooltip cursor={{ fill: 'var(--bg-elevated)' }} content={<CustomTooltip />} />
          <Bar 
            dataKey="total_cost_usd" 
            radius={[0, 4, 4, 0]} 
            barSize={16}
            isAnimationActive={false}
          >
            {data.map((entry, index) => {
               const colorKey = entry.dimension.toLowerCase();
               const fill = CLOUD_COLORS[colorKey] || CLOUD_COLORS.other;
               return <Cell key={`cell-${index}`} fill={fill} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
