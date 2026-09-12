import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { ManagerAnalyticsPage } from '../pages/manager-analytics/ManagerAnalyticsPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ManagerAnalyticsPage />
  </StrictMode>,
);
