import React from 'react';

interface PageSizeSelectorProps {
  value: number;
  onChange: (n: number) => void;
}

export const PageSizeSelector: React.FC<PageSizeSelectorProps> = ({ value, onChange }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label 
        style={{ 
          fontSize: '13px', 
          color: 'var(--text-secondary)',
          whiteSpace: 'nowrap'
        }}
      >
        Rows per page:
      </label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          color: 'var(--text-primary)',
          padding: '4px 24px 4px 12px',
          borderRadius: '6px',
          fontSize: '13px',
          outline: 'none',
          cursor: 'pointer',
          appearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 8px center',
        }}
        onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
        onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
      >
        <option value={25}>25</option>
        <option value={50}>50</option>
        <option value={100}>100</option>
      </select>
    </div>
  );
};
