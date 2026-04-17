import React from 'react';
import { useFilterContext } from '../../context/FilterContext';

export const CloudFilter: React.FC = () => {
  const { cloud, setCloud } = useFilterContext();
  const options = ["all", "aws", "azure", "gcp"] as const;

  return (
    <div style={{ display: 'flex', gap: '4px' }}>
      {options.map((opt) => {
        const isActive = cloud === opt;
        return (
          <button
            key={opt}
            onClick={() => setCloud(opt)}
            style={{
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
              color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              padding: '6px 12px',
              borderRadius: '16px',
              fontSize: '12px',
              fontWeight: 500,
              textTransform: 'uppercase',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              outline: 'none'
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
};
