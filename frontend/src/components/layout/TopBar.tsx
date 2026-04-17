import React from 'react';
import { useLocation } from 'react-router-dom';
import { DateRangePicker } from '../shared/DateRangePicker';
import { CloudFilter } from '../shared/CloudFilter';

export const TopBar: React.FC = () => {
  const location = useLocation();
  
  let pageTitle = "Overview";
  if (location.pathname.startsWith('/anomalies')) pageTitle = "Anomalies";
  if (location.pathname.startsWith('/forecasts')) pageTitle = "Forecasts";
  if (location.pathname.startsWith('/attribution')) pageTitle = "Attribution";

  return (
    <div style={{
      height: '52px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
        {pageTitle}
      </div>
      
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <CloudFilter />
        <DateRangePicker />
      </div>
    </div>
  );
};
