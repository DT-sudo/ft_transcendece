import { getBootstrap } from '../app/http.js';
import { STATUS_OPTIONS } from '../app/shifts.js';

/** Hidden CSRF field for forms that submit natively. */
export function CsrfInput() {
  return <input type="hidden" name="csrfmiddlewaretoken" value={getBootstrap().csrfToken} readOnly />;
}

function Label({ id, label, required }) {
  return (
    <label className="form-label" htmlFor={id}>
      {label}
      {required ? <span aria-hidden="true"> *</span> : null}
    </label>
  );
}

/**
 * Labelled input with an optional hint and the server's validation message.
 * `aria-invalid` and `aria-describedby` tie both to the input for screen readers.
 */
export function Field({ id, label, error, hint, required = false, ...inputProps }) {
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(' ');

  return (
    <div className="mb-4">
      <Label id={id} label={label} required={required} />
      <input
        id={id}
        className={`form-input ${error ? 'form-error' : ''}`}
        required={required}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy || undefined}
        {...inputProps}
      />
      {hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} className="form-error-text" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** onChange handler for filters that apply straight away: submits the control's form. */
export const submitForm = (event) => event.target.form.requestSubmit();

/** Inline "Label: [All ▾]" select over `{ id, name }` options; the empty value means no filter. */
export function FilterSelect({ id, label, options, ...selectProps }) {
  return (
    <div className="flex items-center gap-2">
      <label className="form-label mb-0" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="form-select w-auto" {...selectProps}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Position, worker and status selects shared by the search and analytics filter bars; each submits its form. */
export function ShiftFilterSelects({ filters, positions, workers }) {
  return (
    <>
      <FilterSelect id="positionFilter" name="position" label="Position:" options={positions} defaultValue={filters.position} onChange={submitForm} />
      <FilterSelect id="workerFilter" name="worker" label="Worker:" options={workers} defaultValue={filters.worker} onChange={submitForm} />
      <FilterSelect id="statusFilter" name="status" label="Status:" options={STATUS_OPTIONS} defaultValue={filters.status} onChange={submitForm} />
    </>
  );
}

/** "From [date] to [date]" inputs named `date_from` and `date_to`, for the filter bars. */
export function DateRangeFields({ from, to }) {
  return (
    <div className="flex items-center gap-2">
      <label className="form-label mb-0" htmlFor="dateFrom">
        From
      </label>
      <input id="dateFrom" name="date_from" type="date" className="form-input w-auto" defaultValue={from} />
      <label className="form-label mb-0" htmlFor="dateTo">
        to
      </label>
      <input id="dateTo" name="date_to" type="date" className="form-input w-auto" defaultValue={to} />
    </div>
  );
}

/** Labelled <select> over `{ id, name }` options, with an empty placeholder option first. */
export function SelectField({ id, label, placeholder, options, required = false, ...selectProps }) {
  return (
    <div className="mb-4">
      <Label id={id} label={label} required={required} />
      <select id={id} className="form-select" required={required} {...selectProps}>
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </div>
  );
}
