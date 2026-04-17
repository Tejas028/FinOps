import React from 'react';

export const PageWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div style={{
      padding: '24px',
      width: '100%',
      // minHeight lets it expand
      minHeight: 'calc(100vh - 52px)'
    }}>
      {children}
    </div>
  );
};
