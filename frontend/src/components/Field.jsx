import { useRef, useState } from 'react';

import { formatDayMonthYear, parseDayMonthYear } from '../app/dates.js';
import { getBootstrap } from '../app/http.js';
import { statusOptions } from '../app/shifts.js';
import { t } from '../i18n/index.js';
import { CalendarIcon } from './Icons.jsx';

/**
 * A form that posts natively, with its CSRF token. `fields` are hidden values it posts too
 * (`{ section: 'profile' }`); the server answers with a redirect or re-renders the page.
 */
export function PostForm({ fields = {}, children, ...formProps }) {
  return (
    <form method="post" {...formProps}>
      <input type="hidden" name="csrfmiddlewaretoken" value={getBootstrap().csrfToken} readOnly />
      {Object.entries(fields).map(([name, value]) => (
        <input key={name} type="hidden" name={name} value={value} readOnly />
      ))}
      {children}
    </form>
  );
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
 * Labelled input (or `as="textarea"`) with an optional hint and the server's validation
 * message. `aria-invalid` and `aria-describedby` tie both to the control for screen readers.
 */
export function Field({ id, label, error, hint, required = false, as: Control = 'input', ...inputProps }) {
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(' ');

  return (
    <div className="mb-4">
      <Label id={id} label={label} required={required} />
      <Control
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

/** An account's full name, as the server takes it: two characters at least. */
export function FullNameField(props) {
  return <Field name="full_name" label={t('signup.fullName')} autoComplete="name" required minLength={2} maxLength={150} {...props} />;
}

/** An email address, which is also the login. */
export function EmailField(props) {
  return <Field name="email" type="email" dir="ltr" label={t('login.email')} autoComplete="email" required {...props} />;
}

/**
 * A date typed as DD.MM.YYYY, whatever the browser's own locale would show, with the
 * browser's picker behind the calendar button. The form receives `name` as YYYY-MM-DD,
 * the only format the server reads; `onChange` gets the same ISO date ('' until the
 * text is a real day).
 */
function DateInput({ id, name, defaultValue = '', onChange, required = false, className = '' }) {
  const [iso, setIso] = useState(defaultValue);
  const [text, setText] = useState(() => formatDayMonthYear(defaultValue));
  const textInput = useRef(null);
  const picker = useRef(null);

  const commit = (nextText, nextIso) => {
    setText(nextText);
    setIso(nextIso);
    textInput.current.setCustomValidity(nextText && !nextIso ? t('dates.format') : '');
    onChange?.(nextIso);
  };

  const openPicker = () => {
    try {
      picker.current.showPicker();
    } catch {
      textInput.current.focus();
    }
  };

  return (
    <div className={`date-input ${className}`}>
      <input
        ref={textInput}
        id={id}
        className="form-input"
        type="text"
        dir="ltr"
        inputMode="numeric"
        placeholder={t('dates.placeholder')}
        title={t('dates.format')}
        maxLength={10}
        autoComplete="off"
        required={required}
        value={text}
        onChange={(event) => commit(event.target.value, parseDayMonthYear(event.target.value))}
      />
      <button className="date-input-button" type="button" aria-label={t('dates.pick')} onClick={openPicker}>
        <CalendarIcon />
      </button>
      {/* Only here to open the browser's picker; the typed field above is what people read. */}
      <input
        ref={picker}
        className="date-input-picker"
        type="date"
        tabIndex={-1}
        aria-hidden="true"
        value={iso}
        onChange={(event) => commit(formatDayMonthYear(event.target.value), event.target.value)}
      />
      <input type="hidden" name={name} value={iso} />
    </div>
  );
}

/** Labelled `DateInput`, laid out like `Field`. */
export function DateField({ id, label, required = false, ...inputProps }) {
  return (
    <div className="mb-4">
      <Label id={id} label={label} required={required} />
      <DateInput id={id} required={required} {...inputProps} />
    </div>
  );
}

/** onChange handler for filters that apply straight away: submits the control's form. */
const submitForm = (event) => event.target.form.requestSubmit();

/** An empty option labelled `emptyLabel`, then one per `{ id, name }` option. */
function Options({ emptyLabel, options }) {
  return (
    <>
      <option value="">{emptyLabel}</option>
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          {option.name}
        </option>
      ))}
    </>
  );
}

/** Inline "Label: [All ▾]" select over `{ id, name }` options; the empty value means no filter. */
export function FilterSelect({ id, label, options, ...selectProps }) {
  return (
    <div className="flex items-center gap-2">
      <label className="form-label mb-0" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="form-select w-auto" {...selectProps}>
        <Options emptyLabel={t('common.all')} options={options} />
      </select>
    </div>
  );
}

/** Position, worker and status selects shared by the search and analytics filter bars; each submits its form. */
export function ShiftFilterSelects({ filters, positions, workers }) {
  return (
    <>
      <FilterSelect id="positionFilter" name="position" label={t('filters.position')} options={positions} defaultValue={filters.position} onChange={submitForm} />
      <FilterSelect id="workerFilter" name="worker" label={t('filters.worker')} options={workers} defaultValue={filters.worker} onChange={submitForm} />
      <FilterSelect id="statusFilter" name="status" label={t('filters.status')} options={statusOptions()} defaultValue={filters.status} onChange={submitForm} />
    </>
  );
}

/** "From [date] to [date]" inputs named `date_from` and `date_to`, for the filter bars. */
export function DateRangeFields({ from, to }) {
  return (
    <div className="flex items-center gap-2">
      <label className="form-label mb-0" htmlFor="dateFrom">
        {t('filters.from')}
      </label>
      <DateInput id="dateFrom" name="date_from" className="w-36" defaultValue={from} />
      <label className="form-label mb-0" htmlFor="dateTo">
        {t('filters.to')}
      </label>
      <DateInput id="dateTo" name="date_to" className="w-36" defaultValue={to} />
    </div>
  );
}

/** Labelled <select> over `{ id, name }` options, with an empty placeholder option first. */
export function SelectField({ id, label, placeholder, options, required = false, ...selectProps }) {
  return (
    <div className="mb-4">
      <Label id={id} label={label} required={required} />
      <select id={id} className="form-select" required={required} {...selectProps}>
        <Options emptyLabel={placeholder} options={options} />
      </select>
    </div>
  );
}
