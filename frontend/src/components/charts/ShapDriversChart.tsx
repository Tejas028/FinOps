import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { TopDriver } from '../../types';

interface ShapDriversChartProps {
  data: TopDriver[];
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as TopDriver;
    return (
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        padding: '8px 12px',
        borderRadius: '6px',
        color: 'var(--text-primary)',
        fontSize: '12px',
      }}>
        <p style={{ margin: '0 0 4px 0', color: 'var(--text-secondary)' }}>{data.driver}</p>
        <p style={{ margin: 0, fontWeight: 600 }}>
          Avg SHAP: {data.avg_shap_value.toFixed(2)}
        </p>
      </div>
    );
  }
  return null;
};

export const ShapDriversChart: React.FC<ShapDriversChartProps> = ({ data }) => {
  const chartData = [...data].sort((a, b) => b.avg_shap_value - a.avg_shap_value).slice(0, 8);

  return (
    <div style={{ width: '100%', height: '180px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          data={chartData} 
          layout="vertical" 
          margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
        >
          <XAxis type="number" hide />
          <YAxis 
            type="category" 
            dataKey="driver" 
            stroke="var(--text-secondary)" 
            fontSize={11} 
            tickLine={false}
            axisLine={false}
            width={120}
          />
          <Tooltip cursor={{ fill: 'var(--bg-elevated)' }} content={<CustomTooltip />} />
          <Bar 
            dataKey="avg_shap_value" 
            radius={[0, 4, 4, 0]} 
            barSize={12}
            isAnimationActive={false}
          >
            {chartData.map((entry, index) => {
               const fill = entry.avg_shap_value >= 0 ? 'var(--accent)' : 'var(--text-secondary)';
               return <Cell key={`cell-${index}`} fill={fill} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
