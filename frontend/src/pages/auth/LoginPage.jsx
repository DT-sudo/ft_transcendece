import { getBootstrap } from '../../app/http.js';
import { CsrfInput, Field } from '../../components/Field.jsx';
import { AuthLayout, FormError } from './AuthLayout.jsx';

/** Native form: the browser checks required/type, Django validates and re-renders field errors. */
export function LoginPage() {
  const { data, messages } = getBootstrap();

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your account" messages={messages}>
      {data.showDemo ? (
        <div className="mt-4">
          <a className="btn btn-outline w-full" href={data.urls.demoAdmin}>
            Demo: Admin login
          </a>
          <a className="btn btn-outline mt-3 w-full" href={data.urls.demoManager}>
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

      <FormError message={data.error} />

      <form className="mt-3" method="post" action={data.urls.login}>
        <CsrfInput />

        <Field
          id="email"
          name="username"
          type="email"
          label="Email"
          placeholder="you@example.com"
          autoComplete="email"
          required
          defaultValue={data.email}
          error={data.fieldErrors.email}
        />

        <Field
          id="password"
          name="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          autoComplete="current-password"
          required
          error={data.fieldErrors.password}
        />

        <button type="submit" className="btn btn-primary w-full">
          Sign in
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        New here?{' '}
        <a className="font-medium text-primary hover:underline" href={data.urls.signup}>
          Create a manager account
        </a>
      </p>
    </AuthLayout>
  );
}
