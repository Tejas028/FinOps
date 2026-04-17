import React from 'react';

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title = "No data available", 
  message = "Try adjusting your filters or checking back later." 
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      color: 'var(--text-secondary)',
      border: '1px solid var(--border)',
      background: 'var(--bg-surface)',
      borderRadius: '8px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '8px' }}>
        {title}
      </div>
      <div style={{ fontSize: '12px' }}>
        {message}
      </div>
    </div>
  );
};
