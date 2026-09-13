import { getBootstrap } from '../../app/http.js';
import { CsrfInput, Field } from '../../components/Field.jsx';
import { AuthLayout, FormError } from './AuthLayout.jsx';

/** Native form: the browser checks required/type/length, Django validates and re-renders field errors. */
export function SignUpPage() {
  const { data, messages, urls } = getBootstrap();
  const errors = data.fieldErrors;

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Set up a manager account and start scheduling your team"
      messages={messages}
    >
      <FormError message={data.error} />

      <form className="mt-3" method="post" action={data.urls.signup}>
        <CsrfInput />

        <Field
          id="fullName"
          name="full_name"
          type="text"
          label="Full name"
          placeholder="Jane Doe"
          autoComplete="name"
          required
          minLength={2}
          defaultValue={data.values.fullName}
          error={errors.full_name}
        />

        <Field
          id="email"
          name="email"
          type="email"
          label="Email"
          placeholder="you@example.com"
          autoComplete="email"
          hint="You will use this address to sign in."
          required
          defaultValue={data.values.email}
          error={errors.email}
        />

        <Field
          id="password1"
          name="password1"
          type="password"
          label="Password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
          hint="Minimum 8 characters, not entirely numeric, and not similar to your name or email."
          required
          minLength={8}
          error={errors.password1}
        />

        <Field
          id="password2"
          name="password2"
          type="password"
          label="Confirm password"
          placeholder="Repeat your password"
          autoComplete="new-password"
          required
          minLength={8}
          error={errors.password2}
        />

        <button type="submit" className="btn btn-primary w-full">
          Create account
        </button>
      </form>

      <p className="mt-5 text-center text-xs text-muted-foreground">
        By creating an account you agree to our{' '}
        <a className="underline hover:text-foreground" href={urls.terms}>
          Terms of Service
        </a>{' '}
        and{' '}
        <a className="underline hover:text-foreground" href={urls.privacy}>
          Privacy Policy
        </a>
        .
      </p>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <a className="font-medium text-primary hover:underline" href={data.urls.login}>
          Sign in
        </a>
      </p>

      <p className="mt-4 text-center text-xs text-muted-foreground">
        Employees do not sign up here — your manager creates your account and gives you your
        password.
      </p>
    </AuthLayout>
  );
}
