import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiFetch } from '../api/client';

export interface DataBoundsState {
  minDate: string;
  maxDate: string;
  loading: boolean;
}

const DataBoundsContext = createContext<DataBoundsState>({
  minDate: '2023-01-01',
  maxDate: '2024-12-31',
  loading: true,
});

export const DataBoundsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bounds, setBounds] = useState({ minDate: '2023-01-01', maxDate: '2024-12-31' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    apiFetch<{min_date: string, max_date: string}>('/billing/bounds')
      .then(res => {
        if (active) {
          setBounds({ minDate: res.min_date, maxDate: res.max_date });
        }
      })
      .catch(err => {
        if (active) {
          console.error("Failed to load data bounds:", err);
          // fallback stays at defaults
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  return (
    <DataBoundsContext.Provider value={{ ...bounds, loading }}>
      {children}
    </DataBoundsContext.Provider>
  );
};

export const useDataBounds = () => useContext(DataBoundsContext);
