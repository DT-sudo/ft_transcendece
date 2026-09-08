import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '../styles/index.css';
import { SignUpPage } from '../pages/auth/SignUpPage.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SignUpPage />
  </StrictMode>,
);
