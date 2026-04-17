import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { FilterProvider } from './context/FilterContext';
import { DataBoundsProvider } from './context/DataBoundsContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { PageWrapper } from './components/layout/PageWrapper';
import { OverviewPage } from './pages/OverviewPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { ForecastPage } from './pages/ForecastPage';
import { AttributionPage } from './pages/AttributionPage';
import { AlertsPage } from './pages/AlertsPage';

const App: React.FC = () => {
  return (
    <DataBoundsProvider>
      <FilterProvider>
        <BrowserRouter>
        <div style={{ display: 'flex' }}>
          <Sidebar />
          <div style={{ flex: 1, marginLeft: '220px', display: 'flex', flexDirection: 'column' }}>
            <TopBar />
            <PageWrapper>
              <Routes>
                <Route path="/" element={<OverviewPage />} />
                <Route path="/anomalies" element={<AnomaliesPage />} />
                <Route path="/forecasts" element={<ForecastPage />} />
                <Route path="/attribution" element={<AttributionPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
              </Routes>
            </PageWrapper>
          </div>
        </div>
      </BrowserRouter>
      </FilterProvider>
    </DataBoundsProvider>
  );
};

export default App;
