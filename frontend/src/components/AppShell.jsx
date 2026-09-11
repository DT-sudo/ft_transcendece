import { getBootstrap, submitPost } from '../app/http.js';
import { Dropdown } from './Menus.jsx';
import { ToastProvider } from './Toasts.jsx';

function Header({ user, nav, logoutUrl }) {
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
        {/* The legal pages are public, so there may be nobody signed in. */}
        {user ? (
          <Dropdown
            trigger={({ toggle }) => (
              <button className="btn btn-ghost btn-sm gap-0 p-0" type="button" onClick={toggle} aria-label="User menu">
                <div className="avatar avatar-primary size-8.5">{user.initials}</div>
              </button>
            )}
          >
            <div className="dropdown-item dropdown-item-static font-semibold text-foreground">{user.displayName}</div>
            <div className="dropdown-item dropdown-item-static">{user.role}</div>
            <div className="dropdown-divider" />
            <button
              className="dropdown-item dropdown-item-destructive"
              type="button"
              onClick={() => submitPost(logoutUrl)}
            >
              Logout
            </button>
          </Dropdown>
        ) : null}
      </div>
    </header>
  );
}

/** Site footer with the Privacy Policy and Terms of Service links, reachable signed in or not. */
export function Footer() {
  const { urls } = getBootstrap();

  return (
    <footer className="site-footer">
      <p className="text-sm text-muted-foreground">
        © {new Date().getFullYear()} PlanShift — shift scheduling for hourly teams.
      </p>
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

/** Header, flash-message toasts and footer, shared by every signed-in page. */
export function AppShell({ children }) {
  const { user, nav, urls, messages } = getBootstrap();

  return (
    <ToastProvider initialMessages={messages}>
      <div className="page-with-footer">
        <Header user={user} nav={nav} logoutUrl={urls.logout} />
        <div className="flex-1">{children}</div>
        <Footer />
      </div>
    </ToastProvider>
  );
}
