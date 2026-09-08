// Client-side mirror of the server's form rules.
//
// The server is still the authority — every rule here also exists in the Django
// form — but validating in the browser first means the user sees the problem
// next to the field instead of after a round trip. Each validator returns an
// error string, or '' when the value is acceptable.

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export const MIN_PASSWORD_LENGTH = 8;

export function validateRequired(value, label) {
  return String(value ?? '').trim() ? '' : `${label} is required.`;
}

export function validateFullName(value) {
  const name = String(value ?? '').trim();
  if (!name) return 'Full name is required.';
  if (name.length < 2) return 'Enter your full name.';
  if (name.length > 150) return 'Full name must be at most 150 characters.';
  return '';
}

export function validateEmail(value) {
  const email = String(value ?? '').trim();
  if (!email) return 'Email is required.';
  if (!EMAIL_PATTERN.test(email)) return 'Enter a valid email address.';
  if (email.length > 254) return 'Email must be at most 254 characters.';
  return '';
}

// Mirrors Django's MinimumLength / NumericPassword / UserAttributeSimilarity
// validators closely enough to catch the common mistakes before submitting.
export function validatePassword(value, { email = '', fullName = '' } = {}) {
  const password = String(value ?? '');
  if (!password) return 'Password is required.';
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }
  if (/^\d+$/.test(password)) return 'Password cannot be entirely numeric.';

  const lower = password.toLowerCase();
  const parts = [email.split('@')[0], ...fullName.split(/\s+/)]
    .map((part) => part.trim().toLowerCase())
    .filter((part) => part.length >= 3);
  if (parts.some((part) => lower.includes(part))) {
    return 'Password is too similar to your name or email.';
  }
  return '';
}

export function validatePasswordConfirmation(password, confirmation) {
  if (!confirmation) return 'Confirm your password.';
  if (password !== confirmation) return 'The two passwords do not match.';
  return '';
}

/** Run a {field: validator} map over the form values; returns only real errors. */
export function collectErrors(values, validators) {
  const errors = {};
  for (const [field, validate] of Object.entries(validators)) {
    const message = validate(values[field], values);
    if (message) errors[field] = message;
  }
  return errors;
}
