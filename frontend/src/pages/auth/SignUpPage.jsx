import { useState } from 'react';

import { getBootstrap } from '../../app/bootstrap.js';
import {
  MIN_PASSWORD_LENGTH,
  collectErrors,
  validateEmail,
  validateFullName,
  validatePassword,
  validatePasswordConfirmation,
} from '../../app/validation.js';
import { Field } from '../../components/Field.jsx';
import { CsrfInput } from '../../components/PostForm.jsx';
import { AuthLayout, FormError } from './AuthLayout.jsx';

// Same rules the Django SignUpForm applies, so the browser and the server
// disagree only when the server knows something extra (e.g. email taken).
const VALIDATORS = {
  fullName: (value) => validateFullName(value),
  email: (value) => validateEmail(value),
  password1: (value, values) =>
    validatePassword(value, { email: values.email, fullName: values.fullName }),
  password2: (value, values) => validatePasswordConfirmation(values.password1, value),
};

// Django field name -> the name this form uses for it.
const SERVER_FIELDS = { full_name: 'fullName', email: 'email', password1: 'password1', password2: 'password2' };

function mapServerErrors(fieldErrors = {}) {
  const mapped = {};
  for (const [field, message] of Object.entries(fieldErrors)) {
    mapped[SERVER_FIELDS[field] || field] = message;
  }
  return mapped;
}

export function SignUpPage() {
  const { data, messages } = getBootstrap();

  const [values, setValues] = useState({
    fullName: data.values?.fullName || '',
    email: data.values?.email || '',
    password1: '',
    password2: '',
  });
  const [touched, setTouched] = useState({});
  const [serverErrors, setServerErrors] = useState(mapServerErrors(data.fieldErrors));

  const errors = collectErrors(values, VALIDATORS);

  const update = (field) => (event) => {
    setValues({ ...values, [field]: event.target.value });
    setServerErrors({ ...serverErrors, [field]: '' });
  };
  const blur = (field) => () => setTouched({ ...touched, [field]: true });
  const errorFor = (field) => serverErrors[field] || (touched[field] ? errors[field] : '');

  const submit = (event) => {
    if (Object.keys(errors).length > 0) {
      event.preventDefault();
      setTouched({ fullName: true, email: true, password1: true, password2: true });
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Set up a manager account and start scheduling your team"
      messages={messages || []}
    >
      <FormError message={data.error} />

      <form className="mt-3" method="post" action={data.urls.signup} noValidate onSubmit={submit}>
        <CsrfInput />

        <Field
          id="fullName"
          name="full_name"
          type="text"
          label="Full name"
          placeholder="Jane Doe"
          autoComplete="name"
          required
          value={values.fullName}
          error={errorFor('fullName')}
          onChange={update('fullName')}
          onBlur={blur('fullName')}
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
          value={values.email}
          error={errorFor('email')}
          onChange={update('email')}
          onBlur={blur('email')}
        />

        <Field
          id="password1"
          name="password1"
          type="password"
          label="Password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
          hint={`Minimum ${MIN_PASSWORD_LENGTH} characters, not entirely numeric, and not similar to your name or email.`}
          required
          value={values.password1}
          error={errorFor('password1')}
          onChange={update('password1')}
          onBlur={blur('password1')}
        />

        <Field
          id="password2"
          name="password2"
          type="password"
          label="Confirm password"
          placeholder="Repeat your password"
          autoComplete="new-password"
          required
          value={values.password2}
          error={errorFor('password2')}
          onChange={update('password2')}
          onBlur={blur('password2')}
        />

        <button type="submit" className="btn btn-primary w-full">
          Create account
        </button>
      </form>

      <p className="mt-5 text-center text-xs text-muted-foreground">
        By creating an account you agree to our{' '}
        <a className="underline hover:text-foreground" href={getBootstrap().urls?.terms || '/terms/'}>
          Terms of Service
        </a>{' '}
        and{' '}
        <a className="underline hover:text-foreground" href={getBootstrap().urls?.privacy || '/privacy/'}>
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
