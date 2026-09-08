import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { LegalPage } from '../pages/legal/LegalPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LegalPage />
  </StrictMode>,
);
