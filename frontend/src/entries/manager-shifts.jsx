import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { ManagerShiftsPage } from '../pages/manager-shifts/ManagerShiftsPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ManagerShiftsPage />
  </StrictMode>,
);
