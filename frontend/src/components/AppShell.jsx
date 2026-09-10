import { useState } from 'react';

import { getBootstrap, submitPost } from '../app/http.js';
import { ConfirmModal } from './Modal.jsx';
import { Dropdown } from './Menus.jsx';
import { ToastProvider } from './Toasts.jsx';

function Header({ user, nav, onLogout }) {
  return (
    <header className="sticky top-0 z-45 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 border-b border-border bg-card px-4 py-1.5 shadow-header">
      <div />

      <nav className="flex items-center justify-center gap-2" aria-label="Primary">
        {nav.map((link) => (
          <a key={link.href} href={link.href} className={`nav-link ${link.active ? 'nav-link-active' : ''}`}>
            {link.label}
          </a>
        ))}
      </nav>

      <div className="justify-self-end">
        <Dropdown
          trigger={({ toggle }) => (
            <button className="btn btn-ghost btn-sm gap-0 p-0" type="button" onClick={toggle} aria-label="User menu">
              <div className="avatar avatar-primary size-8.5">{user.initials}</div>
            </button>
          )}
        >
          {({ close }) => (
            <>
              <div className="dropdown-item dropdown-item-static font-semibold text-foreground">{user.displayName}</div>
              <div className="dropdown-item dropdown-item-static">{user.role}</div>
              <div className="dropdown-divider" />
              <button
                className="dropdown-item dropdown-item-destructive"
                type="button"
                onClick={() => {
                  close();
                  onLogout();
                }}
              >
                Logout
              </button>
            </>
          )}
        </Dropdown>
      </div>
    </header>
  );
}

/** Site footer with the Privacy Policy and Terms of Service links, reachable signed in or not. */
export function Footer() {
  const { urls } = getBootstrap();

  return (
    <footer className="site-footer">
      <p className="text-sm text-muted-foreground">© {new Date().getFullYear()} PlanShift — shift scheduling for hourly teams.</p>
      <nav className="flex items-center gap-4" aria-label="Legal">
        <a className="footer-link" href={urls.privacy}>
          Privacy Policy
        </a>
        <a className="footer-link" href={urls.terms}>
          Terms of Service
        </a>
      </nav>
    </footer>
  );
}

/** Header, flash-message toasts and the logout confirmation, shared by every signed-in page. */
export function AppShell({ children }) {
  const { user, nav, urls, messages } = getBootstrap();
  const [confirmLogout, setConfirmLogout] = useState(false);

  return (
    <ToastProvider initialMessages={messages}>
      <div className="page-with-footer">
        <Header user={user} nav={nav} onLogout={() => setConfirmLogout(true)} />
        <div className="flex-1">{children}</div>
        <Footer />
      </div>

      {confirmLogout ? (
        <ConfirmModal
          title="Confirm logout"
          message="Do you really want to log out?"
          maxWidth="480px"
          onCancel={() => setConfirmLogout(false)}
          onConfirm={() => submitPost(urls.logout)}
        />
      ) : null}
    </ToastProvider>
  );
}
