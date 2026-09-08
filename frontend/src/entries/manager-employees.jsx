import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { ManagerEmployeesPage } from '../pages/manager-employees/ManagerEmployeesPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ManagerEmployeesPage />
  </StrictMode>,
);
