// All dates travel as ISO strings (YYYY-MM-DD); labels are formatted here in the page's language.
import { firstDayOfWeek, intlLocale, t } from '../i18n/index.js';

export const pad2 = (value) => String(value).padStart(2, '0');

const toISODate = (date) => `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;

const dateFromISO = (iso) => new Date(`${iso}T00:00:00`);

export function addMonths(iso, months) {
  const date = dateFromISO(iso);
  date.setMonth(date.getMonth() + months);
  return toISODate(date);
}

export function addDays(iso, days) {
  const date = dateFromISO(iso);
  date.setDate(date.getDate() + days);
  return toISODate(date);
}

/** The seven days from `startISO`, each with its short weekday name and day of the month. */
export function weekDays(startISO) {
  return Array.from({ length: 7 }, (_, index) => {
    const iso = addDays(startISO, index);
    const date = dateFromISO(iso);
    return { iso, label: date.toLocaleDateString(intlLocale(), { weekday: 'short' }), dayNumber: date.getDate() };
  });
}

/** The 6x7 day matrix a month view paints, starting on the language's first day of the week. */
export function monthMatrix(anchorISO, todayISO) {
  const anchor = dateFromISO(anchorISO);
  const month = anchor.getMonth();
  const first = new Date(anchor.getFullYear(), month, 1);
  const daysBefore = (first.getDay() - firstDayOfWeek() + 7) % 7;

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(first.getFullYear(), month, 1 - daysBefore + index);
    const iso = toISODate(date);
    return { iso, dayNumber: date.getDate(), inMonth: date.getMonth() === month, isToday: iso === todayISO };
  });
}

/** Short weekday names in the order `monthMatrix` lays out its columns. */
export function weekdayLabels() {
  // 1 January 2023 was a Sunday (day 0).
  return Array.from({ length: 7 }, (_, index) =>
    new Date(2023, 0, 1 + ((firstDayOfWeek() + index) % 7)).toLocaleDateString(intlLocale(), { weekday: 'short' }),
  );
}

/** "09:30" -> 570. */
export const minutesOf = (time) => {
  const [hours, minutes] = time.split(':').map(Number);
  return hours * 60 + minutes;
};

export const shiftDurationMinutes = (shift) => minutesOf(shift.end_time) - minutesOf(shift.start_time);

const inUnit = (value, unit) => new Intl.NumberFormat(intlLocale(), { style: 'unit', unit, unitDisplay: 'narrow' }).format(value);

/** "8h", "7h 30m", "45m" ("7 h 30 min" in Czech). */
export function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return [hours && inUnit(hours, 'hour'), (rest || !hours) && inUnit(rest, 'minute')].filter(Boolean).join(' ');
}

/** "12.5h": a number of hours, possibly fractional. */
export const formatHours = (hours) => inUnit(hours, 'hour');

/** "September 2026". */
export const formatMonth = (iso) => dateFromISO(iso).toLocaleDateString(intlLocale(), { month: 'long', year: 'numeric' });

/** "Sat, 19 Sept 2026", or "Sat, 19 Sept" without the year. */
export function formatDate(iso, { year = true } = {}) {
  return dateFromISO(iso).toLocaleDateString(intlLocale(), {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: year ? 'numeric' : undefined,
  });
}

/** Today's date and time, for a report's "Generated" line. */
export const formatNow = () => new Date().toLocaleString(intlLocale());

const RELATIVE_UNITS = [
  ['year', 365 * 86400],
  ['month', 30 * 86400],
  ['week', 7 * 86400],
  ['day', 86400],
  ['hour', 3600],
  ['minute', 60],
];

/** "5 minutes ago", "yesterday", "just now" for an ISO timestamp. */
export function timeAgo(isoDateTime) {
  const seconds = (Date.parse(isoDateTime) - Date.now()) / 1000;
  const format = new Intl.RelativeTimeFormat(intlLocale(), { numeric: 'auto' });
  for (const [unit, length] of RELATIVE_UNITS) {
    if (Math.abs(seconds) >= length) return format.format(Math.round(seconds / length), unit);
  }
  return t('dates.justNow');
}

/** Merge query parameters into the current URL and reload the page; empty values are dropped. */
export function navigateWith(params) {
  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(params)) {
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  }
  window.location.assign(`${url.pathname}?${url.searchParams}`);
}
