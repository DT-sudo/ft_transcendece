import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import './styles/index.css';
import { getBootstrap } from './app/http.js';
import { useLanguage } from './i18n/index.js';
import { LoginPage } from './pages/auth/LoginPage.jsx';
import { SignUpPage } from './pages/auth/SignUpPage.jsx';
import { TwoFactorVerifyPage } from './pages/auth/TwoFactorVerifyPage.jsx';
import { EmployeeShiftsPage } from './pages/employee-shifts/EmployeeShiftsPage.jsx';
import { LegalPage } from './pages/legal/LegalPage.jsx';
import { ManagerAnalyticsPage } from './pages/manager-analytics/ManagerAnalyticsPage.jsx';
import { ManagerEmployeesPage } from './pages/manager-employees/ManagerEmployeesPage.jsx';
import { ManagerShiftSearchPage } from './pages/manager-shift-search/ManagerShiftSearchPage.jsx';
import { ManagerShiftsPage } from './pages/manager-shifts/ManagerShiftsPage.jsx';
import { PrivacyCenterPage } from './pages/privacy/PrivacyCenterPage.jsx';
import { FriendsPage } from './pages/profiles/FriendsPage.jsx';
import { ProfilePage } from './pages/profiles/ProfilePage.jsx';
import { AccountSettingsPage } from './pages/profiles/AccountSettingsPage.jsx';

// Django names the page in the payload (`render_app(page=...)`); one bundle serves them all.
const PAGES = {
  login: LoginPage,
  signup: SignUpPage,
  'two-factor-verify': TwoFactorVerifyPage,
  legal: LegalPage,
  'manager-shifts': ManagerShiftsPage,
  'manager-shift-search': ManagerShiftSearchPage,
  'manager-analytics': ManagerAnalyticsPage,
  'manager-employees': ManagerEmployeesPage,
  'employee-shifts': EmployeeShiftsPage,
  'privacy-center': PrivacyCenterPage,
  profile: ProfilePage,
  'account-settings': AccountSettingsPage,
  friends: FriendsPage,
};

const Page = PAGES[getBootstrap().page];

/** Re-renders the whole page when the language changes, in place: open modals and typed input survive. */
function App() {
  useLanguage();
  return <Page />;
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
