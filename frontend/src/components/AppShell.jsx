import { useRef, useState } from 'react';

import { getBootstrap } from '../app/bootstrap.js';
import { ConfirmModal } from './Modal.jsx';
import { Dropdown } from './Menus.jsx';
import { PostForm } from './PostForm.jsx';
import { ToastProvider } from './Toasts.jsx';
import { usePublishedHeight } from './hooks.js';

function Header({ user, nav, onLogout }) {
  const headerRef = usePublishedHeight('--header-sticky-height');

  return (
    <header
      ref={headerRef}
      className="sticky top-0 z-45 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 border-b border-border bg-card px-4 py-1.5 shadow-header"
    >
      <div />

      <nav className="flex items-center justify-center gap-2" aria-label="Primary">
        {(nav || []).map((link) => (
          <a
            key={link.href}
            href={link.href}
            className={`nav-link ${link.active ? 'nav-link-active' : ''}`}
          >
            {link.label}
          </a>
        ))}
      </nav>

      <div className="justify-self-end">
        <Dropdown
          trigger={({ toggle }) => (
            <button
              className="btn btn-ghost btn-sm gap-0 p-0"
              type="button"
              onClick={toggle}
              aria-label="User menu"
            >
              <div className="avatar avatar-primary size-8.5" aria-label="User avatar">
                {user?.initials || 'U'}
              </div>
            </button>
          )}
        >
          {({ close }) => (
            <>
              <div className="dropdown-item dropdown-item-static font-semibold text-foreground">
                {user?.displayName || 'User'}
              </div>
              <div className="dropdown-item dropdown-item-static">{user?.role || 'User'}</div>
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

/** Header, flash-message toasts and the logout confirmation, shared by every page. */
export function AppShell({ children }) {
  const { user, nav, urls, messages } = getBootstrap();
  const [confirmLogout, setConfirmLogout] = useState(false);
  const logoutFormRef = useRef(null);

  return (
    <ToastProvider initialMessages={messages || []}>
      <Header user={user} nav={nav} onLogout={() => setConfirmLogout(true)} />

      {children}

      <PostForm formRef={logoutFormRef} action={urls?.logout || '/logout/'} />

      {confirmLogout ? (
        <ConfirmModal
          title="Confirm logout"
          message="Are you really want to log out?"
          maxWidth="480px"
          confirmText="Yes"
          cancelText="No"
          onCancel={() => setConfirmLogout(false)}
          onConfirm={() => logoutFormRef.current?.submit()}
        />
      ) : null}
    </ToastProvider>
  );
}
