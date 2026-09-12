import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { ManagerShiftSearchPage } from '../pages/manager-shift-search/ManagerShiftSearchPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ManagerShiftSearchPage />
  </StrictMode>,
);
