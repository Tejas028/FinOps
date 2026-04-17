import React, { createContext, useContext, useState, useEffect } from 'react';
import { format, subDays } from 'date-fns';

export interface FilterState {
  startDate: string;
  endDate: string;
  cloud: "all" | "aws" | "azure" | "gcp";
}

interface FilterContextType extends FilterState {
  setStartDate: (date: string) => void;
  setEndDate: (date: string) => void;
  setCloud: (cloud: FilterState["cloud"]) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

import { useDataBounds } from './DataBoundsContext';

export const FilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { maxDate, loading } = useDataBounds();
  
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [cloud, setCloud] = useState<FilterState["cloud"]>("all");

  // Sync with actual bounds once loaded
  useEffect(() => {
    if (!loading && maxDate) {
      setEndDate(maxDate);
      setStartDate(format(subDays(new Date(maxDate), 365), 'yyyy-MM-dd'));
    }
  }, [loading, maxDate]);

  // Give a default render state while loading bounds
  if (loading || !startDate || !endDate) return null;

  return (
    <FilterContext.Provider value={{ startDate, setStartDate, endDate, setEndDate, cloud, setCloud }}>
      {children}
    </FilterContext.Provider>
  );
};

export const useFilterContext = () => {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilterContext must be used within a FilterProvider');
  }
  return context;
};
