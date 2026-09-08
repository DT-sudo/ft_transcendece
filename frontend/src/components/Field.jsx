/**
 * Labelled input with its validation message.
 *
 * Errors are shown once the field has been touched or the form submitted, so a
 * user is not told the email is invalid while they are still on the first
 * character. `aria-invalid` and `aria-describedby` tie the message to the input
 * for screen readers.
 */
export function Field({
  id,
  label,
  error,
  hint,
  required = false,
  children,
  ...inputProps
}) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ');

  return (
    <div className="mb-4">
      <label className="form-label" htmlFor={id}>
        {label}
        {required ? <span aria-hidden="true"> *</span> : null}
      </label>

      {children ?? (
        <input
          id={id}
          className={`form-input ${error ? 'form-error' : ''}`}
          required={required}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy || undefined}
          {...inputProps}
        />
      )}

      {hint ? (
        <p id={hintId} className="mt-1.5 text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}

      {error ? (
        <p id={errorId} className="form-error-text" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
