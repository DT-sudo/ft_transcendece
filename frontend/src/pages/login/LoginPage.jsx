import { getBootstrap } from '../../app/bootstrap.js';
import { CsrfInput } from '../../components/PostForm.jsx';
import { ToastProvider } from '../../components/Toasts.jsx';

export function LoginPage() {
  const { data, messages } = getBootstrap();

  return (
    <ToastProvider initialMessages={messages || []}>
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-105 rounded-panel border border-border bg-card p-7 shadow-[0_20px_50px_rgb(0_0_0_/_0.10)]">
          <div className="mt-4 mb-5 text-center">
            <h2 className="text-2xl tracking-tight">Welcome back</h2>
            <p className="mt-1.5 text-muted-foreground">Sign in to your account</p>
          </div>

          {data.showDemo ? (
            <div className="mt-4">
              <a className="btn btn-outline w-full" href={data.urls.demoManager}>
                Demo: Manager login
              </a>
              <a className="btn btn-outline mt-3 w-full" href={data.urls.demoEmployee}>
                Demo: Employee login
              </a>

              <div className="my-6 flex items-center">
                <div className="h-px flex-1 bg-border" />
                <span className="px-4 text-xs uppercase text-muted-foreground">or</span>
                <div className="h-px flex-1 bg-border" />
              </div>
            </div>
          ) : null}

          {data.error ? (
            <div className="card mb-4 p-3">
              <div className="text-sm text-destructive">{data.error}</div>
            </div>
          ) : null}

          <form className="mt-3" method="post" action={data.urls.login}>
            <CsrfInput />

            <div className="mb-4">
              <label className="form-label" htmlFor="username">
                Email / Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                className="form-input"
                placeholder="Enter your email"
                required
                defaultValue={data.username || ''}
              />
            </div>

            <div className="mb-4">
              <label className="form-label" htmlFor="password">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder="Enter your password"
                required
              />
            </div>

            <button type="submit" className="btn btn-primary w-full">
              Sign in
            </button>
          </form>
        </div>
      </div>
    </ToastProvider>
  );
}
