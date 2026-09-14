import { getBootstrap, submitPost } from '../app/http.js';
import { Avatar } from './Avatar.jsx';
import { Dropdown } from './Menus.jsx';
import { NotificationBell, ToastProvider } from './Notifications.jsx';

function Header({ user, nav, urls }) {
  return (
    <header className="sticky top-0 z-45 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 border-b border-border bg-card px-4 py-1.5 shadow-header">
      <div>{user ? <NotificationBell /> : null}</div>

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
                <Avatar name={user.fullName} src={user.avatarUrl} size="header" primary />
              </button>
            )}
          >
            <div className="dropdown-item dropdown-item-static font-semibold text-foreground">{user.fullName}</div>
            <div className="dropdown-item dropdown-item-static">{user.role}</div>
            <div className="dropdown-divider" />
            <a className="dropdown-item" href={user.profileUrl}>
              My profile
            </a>
            <a className="dropdown-item" href={urls.settings}>
              Account settings
            </a>
            <a className="dropdown-item" href={urls.privacyCenter}>
              Privacy & my data
            </a>
            <button
              className="dropdown-item dropdown-item-destructive"
              type="button"
              onClick={() => submitPost(urls.logout)}
            >
              Logout
            </button>
          </Dropdown>
        ) : null}
      </div>
    </header>
  );
}

/** Pinned footer with the Privacy Policy and Terms of Service links, reachable signed in or not; `children` go in the middle. */
export function Footer({ children }) {
  const { urls } = getBootstrap();

  return (
    <footer className="site-footer">
      <p className="text-xs text-muted-foreground">
        © {new Date().getFullYear()} PlanShift — shift scheduling for hourly teams.
      </p>
      {children}
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

/** Header, flash-message toasts and footer, shared by every signed-in page; `footer` adds page content to the footer bar. */
export function AppShell({ children, footer }) {
  const { user, nav, urls, messages, notifications } = getBootstrap();

  return (
    <ToastProvider initialMessages={messages} notifications={notifications}>
      <div className="page-with-footer">
        <Header user={user} nav={nav} urls={urls} />
        <div className="flex-1">{children}</div>
        <Footer>{footer}</Footer>
      </div>
    </ToastProvider>
  );
}
