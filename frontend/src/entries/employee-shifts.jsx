import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { EmployeeShiftsPage } from '../pages/employee-shifts/EmployeeShiftsPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <EmployeeShiftsPage />
  </StrictMode>,
);
