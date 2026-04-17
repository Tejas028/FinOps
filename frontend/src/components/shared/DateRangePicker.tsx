import React, { useState } from 'react';
import { useFilterContext } from '../../context/FilterContext';
import { useDataBounds } from '../../context/DataBoundsContext';
import { subDays } from 'date-fns';

export const DateRangePicker: React.FC = () => {
  const { startDate, setStartDate, endDate, setEndDate } = useFilterContext();
  const { minDate, maxDate } = useDataBounds();
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const format = (date: Date) => date.toISOString().split('T')[0];

  const presets = [
    { label: '30D', days: 30 },
    { label: '90D', days: 90 },
    { label: '6M', days: 180 },
    { label: '1Y', days: 365 },
    { label: 'ALL', days: 0 }
  ];

  const handlePresetClick = (label: string, days: number) => {
    if (!maxDate) return;
    
    const end = new Date(maxDate);
    let start: Date;
    
    if (label === 'ALL') {
      start = new Date(minDate || '2023-01-01');
    } else {
      start = subDays(end, days);
      const min = new Date(minDate || '2023-01-01');
      if (start < min) start = min;
    }
    
    setStartDate(format(start));
    setEndDate(format(end));
    setActivePreset(label);
  };

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    borderRadius: '6px',
    padding: '6px 10px',
    fontSize: '13px',
    outline: 'none',
  };

  const pillStyle = (isActive: boolean): React.CSSProperties => ({
    border: isActive ? '1px solid #F59E0B' : '1px solid #2A2A3D',
    color: isActive ? '#F59E0B' : '#7B7B96',
    background: isActive ? 'rgba(245, 158, 11, 0.08)' : 'transparent',
    borderRadius: '20px',
    padding: '4px 12px',
    fontSize: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    outline: 'none',
  });

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        {presets.map(p => (
          <button
            key={p.label}
            style={pillStyle(activePreset === p.label)}
            onClick={() => handlePresetClick(p.label, p.days)}
            onMouseEnter={(e) => {
              if (activePreset !== p.label) e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.6)';
            }}
            onMouseLeave={(e) => {
              if (activePreset !== p.label) e.currentTarget.style.borderColor = '#2A2A3D';
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div style={{ height: '20px', width: '1px', background: '#2A2A3D' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <input
          type="date"
          value={startDate}
          min={minDate}
          max={maxDate}
          onChange={(e) => {
            setStartDate(e.target.value);
            setActivePreset(null);
          }}
          style={inputStyle}
        />
        <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>to</span>
        <input
          type="date"
          value={endDate}
          min={minDate}
          max={maxDate}
          onChange={(e) => {
            setEndDate(e.target.value);
            setActivePreset(null);
          }}
          style={inputStyle}
        />
      </div>
    </div>
  );
};
