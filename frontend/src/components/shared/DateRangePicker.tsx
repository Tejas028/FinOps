import React from 'react';
import { useFilterContext } from '../../context/FilterContext';
import { useDataBounds } from '../../context/DataBoundsContext';

export const DateRangePicker: React.FC = () => {
  const { startDate, setStartDate, endDate, setEndDate } = useFilterContext();
  const { minDate, maxDate } = useDataBounds();

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    borderRadius: '6px',
    padding: '6px 10px',
    fontSize: '13px',
    outline: 'none',
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <input
        type="date"
        value={startDate}
        min={minDate}
        max={maxDate}
        onChange={(e) => setStartDate(e.target.value)}
        style={inputStyle}
      />
      <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>to</span>
      <input
        type="date"
        value={endDate}
        min={minDate}
        max={maxDate}
        onChange={(e) => setEndDate(e.target.value)}
        style={inputStyle}
      />
    </div>
  );
};
