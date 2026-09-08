import { getBootstrap } from '../app/bootstrap.js';

/**
 * Site footer. Carries the Privacy Policy and Terms of Service links, which the
 * shell injects into every page's payload so they are reachable from anywhere,
 * signed in or not.
 */
export function Footer() {
  const { urls } = getBootstrap();
  const year = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <p className="text-sm text-muted-foreground">
        © {year} PlanShift — shift scheduling for hourly teams.
      </p>
      <nav className="flex items-center gap-4" aria-label="Legal">
        <a className="footer-link" href={urls?.privacy || '/privacy/'}>
          Privacy Policy
        </a>
        <a className="footer-link" href={urls?.terms || '/terms/'}>
          Terms of Service
        </a>
      </nav>
    </footer>
  );
}
