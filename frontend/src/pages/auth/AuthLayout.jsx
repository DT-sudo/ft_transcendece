import { Footer } from '../../components/AppShell.jsx';
import { ToastProvider } from '../../components/Toasts.jsx';

/** Centred card used by both the login and the sign-up page. */
export function AuthLayout({ title, subtitle, messages = [], children }) {
  return (
    <ToastProvider initialMessages={messages}>
      <div className="page-with-footer">
        <main className="flex flex-1 items-center justify-center p-6">
          <div className="w-full max-w-105 rounded-panel border border-border bg-card p-7 shadow-[0_20px_50px_rgb(0_0_0_/_0.10)]">
            <div className="mt-4 mb-5 text-center">
              <h1 className="text-2xl tracking-tight">{title}</h1>
              <p className="mt-1.5 text-muted-foreground">{subtitle}</p>
            </div>

            {children}
          </div>
        </main>

        <Footer />
      </div>
    </ToastProvider>
  );
}

/** Non-field error returned by the server, e.g. "Incorrect email or password." */
export function FormError({ message }) {
  if (!message) return null;
  return (
    <div className="card mb-4 p-3" role="alert">
      <div className="text-sm text-destructive">{message}</div>
    </div>
  );
}
