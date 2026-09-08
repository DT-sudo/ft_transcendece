import { useState } from 'react';

import { getBootstrap } from '../../app/bootstrap.js';
import { collectErrors, validateEmail, validateRequired } from '../../app/validation.js';
import { Field } from '../../components/Field.jsx';
import { CsrfInput } from '../../components/PostForm.jsx';
import { AuthLayout, FormError } from './AuthLayout.jsx';

const VALIDATORS = {
  email: (value) => validateEmail(value),
  password: (value) => validateRequired(value, 'Password'),
};

export function LoginPage() {
  const { data, messages } = getBootstrap();

  const [values, setValues] = useState({ email: data.email || '', password: '' });
  const [touched, setTouched] = useState({});
  // Errors the server sent back are shown until the field is edited again.
  const [serverErrors, setServerErrors] = useState(data.fieldErrors || {});

  const errors = collectErrors(values, VALIDATORS);

  const update = (field) => (event) => {
    setValues({ ...values, [field]: event.target.value });
    setServerErrors({ ...serverErrors, [field]: '' });
  };
  const blur = (field) => () => setTouched({ ...touched, [field]: true });
  const errorFor = (field) => serverErrors[field] || (touched[field] ? errors[field] : '');

  const submit = (event) => {
    // The browser's own required/type checks run first; this catches the rest
    // and keeps the message identical to the one the server would return.
    if (Object.keys(errors).length > 0) {
      event.preventDefault();
      setTouched({ email: true, password: true });
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your account" messages={messages || []}>
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

      <FormError message={data.error} />

      <form className="mt-3" method="post" action={data.urls.login} noValidate onSubmit={submit}>
        <CsrfInput />

        <Field
          id="email"
          name="username"
          type="email"
          label="Email"
          placeholder="you@example.com"
          autoComplete="email"
          required
          value={values.email}
          error={errorFor('email')}
          onChange={update('email')}
          onBlur={blur('email')}
        />

        <Field
          id="password"
          name="password"
          type="password"
          label="Password"
          placeholder="Enter your password"
          autoComplete="current-password"
          required
          value={values.password}
          error={errorFor('password')}
          onChange={update('password')}
          onBlur={blur('password')}
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
