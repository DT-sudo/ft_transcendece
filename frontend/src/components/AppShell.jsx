import { getBootstrap, submitPost } from '../app/http.js';
import { useSessionGuard } from '../app/session.js';
import { t } from '../i18n/index.js';
import { Avatar } from './Avatar.jsx';
import { LanguageSwitcher } from './LanguageSwitcher.jsx';
import { Dropdown } from './Menus.jsx';
import { NotificationBell, ToastProvider } from './Notifications.jsx';

function Header({ user, nav, urls }) {
  return (
    <header className="sticky top-0 z-45 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 border-b border-border bg-card px-4 py-1.5 shadow-header">
      <div>{user ? <NotificationBell /> : null}</div>

      <nav className="flex items-center justify-center gap-2" aria-label={t('nav.primary')}>
        {nav.map((link) => (
          <a key={link.href} href={link.href} className={`nav-link ${link.active ? 'nav-link-active' : ''}`}>
            {t(`nav.${link.id}`)}
          </a>
        ))}
      </nav>

      <div className="justify-self-end">
        {/* The legal pages are public, so there may be nobody signed in. */}
        {user ? (
          <Dropdown
            trigger={({ toggle }) => (
              <button className="btn btn-ghost btn-sm gap-0 p-0" type="button" onClick={toggle} aria-label={t('header.userMenu')}>
                <Avatar name={user.fullName} src={user.avatarUrl} size="header" primary />
              </button>
            )}
          >
            <div className="dropdown-item dropdown-item-static font-semibold text-foreground">{user.fullName}</div>
            <div className="dropdown-item dropdown-item-static">{user.role}</div>
            <div className="dropdown-divider" />
            <a className="dropdown-item" href={user.profileUrl}>
              {t('header.myProfile')}
            </a>
            <a className="dropdown-item" href={urls.settings}>
              {t('header.accountSettings')}
            </a>
            <a className="dropdown-item" href={urls.privacyCenter}>
              {t('header.privacy')}
            </a>
            <button
              className="dropdown-item dropdown-item-destructive"
              type="button"
              onClick={() => submitPost(urls.logout)}
            >
              {t('header.logout')}
            </button>
          </Dropdown>
        ) : null}
      </div>
    </header>
  );
}

/**
 * Pinned footer on every page, signed in or not: the language switcher and the Privacy Policy and
 * Terms of Service links; `children` go in the middle.
 */
export function Footer({ children }) {
  const { urls } = getBootstrap();

  return (
    <footer className="site-footer">
      <p className="text-xs text-muted-foreground">{t('footer.tagline', { year: new Date().getFullYear() })}</p>
      {children}
      <div className="flex flex-wrap items-center gap-4">
        <LanguageSwitcher id="footerLanguage" />
        <nav className="flex items-center gap-4" aria-label={t('footer.legal')}>
          <PrivacyPolicyLink />
          <a className="footer-link" href={urls.terms}>
            {t('footer.terms')}
          </a>
        </nav>
      </div>
    </footer>
  );
}

/** A page's title card: an icon, the title (and `subtitle`), and `children` at the end. */
export function PageHeader({ icon: Icon, title, subtitle = null, children = null }) {
  return (
    <div className="card page-toolbar-card">
      <div className="flex flex-wrap items-center gap-3">
        <Icon size={20} className="text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <h1 className="card-title">{title}</h1>
          {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
        </div>
        {children}
      </div>
    </div>
  );
}

/** The Privacy Policy, linked from running text. */
export function PrivacyPolicyLink() {
  return (
    <a className="footer-link" href={getBootstrap().urls.privacy}>
      {t('footer.privacyPolicy')}
    </a>
  );
}

/** Header, flash-message toasts and footer, shared by every signed-in page; `footer` adds page content to the footer bar. */
export function AppShell({ children, footer }) {
  const { user, nav, urls, messages, notifications } = getBootstrap();
  useSessionGuard();

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
