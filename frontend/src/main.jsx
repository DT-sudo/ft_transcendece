import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import './styles/index.css';
import { getBootstrap } from './app/http.js';
import { LoginPage } from './pages/auth/LoginPage.jsx';
import { SignUpPage } from './pages/auth/SignUpPage.jsx';
import { EmployeeShiftsPage } from './pages/employee-shifts/EmployeeShiftsPage.jsx';
import { LegalPage } from './pages/legal/LegalPage.jsx';
import { ManagerEmployeesPage } from './pages/manager-employees/ManagerEmployeesPage.jsx';
import { ManagerShiftsPage } from './pages/manager-shifts/ManagerShiftsPage.jsx';

// Django names the page in the payload (`render_app(page=...)`); one bundle serves them all.
const PAGES = {
  login: LoginPage,
  signup: SignUpPage,
  legal: LegalPage,
  'manager-shifts': ManagerShiftsPage,
  'manager-employees': ManagerEmployeesPage,
  'employee-shifts': EmployeeShiftsPage,
};

const Page = PAGES[getBootstrap().page];

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Page />
  </StrictMode>,
);
