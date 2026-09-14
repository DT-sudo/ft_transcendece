// All dates travel as ISO strings (YYYY-MM-DD); labels are formatted here in the browser's language.

const pad2 = (value) => String(value).padStart(2, '0');

const toISODate = (date) => `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;

const dateFromISO = (iso) => new Date(`${iso}T00:00:00`);

export function addMonths(iso, months) {
  const date = dateFromISO(iso);
  date.setMonth(date.getMonth() + months);
  return toISODate(date);
}

/** The 6x7 day matrix a month view paints, starting on Sunday. */
export function monthMatrix(anchorISO, todayISO) {
  const anchor = dateFromISO(anchorISO);
  const month = anchor.getMonth();
  const first = new Date(anchor.getFullYear(), month, 1);

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(first.getFullYear(), month, 1 - first.getDay() + index);
    const iso = toISODate(date);
    return { iso, dayNumber: date.getDate(), inMonth: date.getMonth() === month, isToday: iso === todayISO };
  });
}

/** "09:30" -> 570. */
const minutesOf = (time) => {
  const [hours, minutes] = time.split(':').map(Number);
  return hours * 60 + minutes;
};

export const shiftDurationMinutes = (shift) => minutesOf(shift.end_time) - minutesOf(shift.start_time);

/** "8h", "7h 30m", "45m". */
export function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return [hours && `${hours}h`, (rest || !hours) && `${rest}m`].filter(Boolean).join(' ');
}

/** "September 2026". */
export const formatMonth = (iso) => dateFromISO(iso).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });

/** Short weekday names Sunday..Saturday. */
export const WEEKDAY_LABELS = Array.from({ length: 7 }, (_, day) =>
  new Date(2023, 0, 1 + day).toLocaleDateString(undefined, { weekday: 'short' }),
);

/** "Sat, 19 Sept 2026", or "Sat, 19 Sept" without the year. */
export function formatDate(iso, { year = true } = {}) {
  return dateFromISO(iso).toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: year ? 'numeric' : undefined,
  });
}

const RELATIVE_UNITS = [
  ['year', 365 * 86400],
  ['month', 30 * 86400],
  ['week', 7 * 86400],
  ['day', 86400],
  ['hour', 3600],
  ['minute', 60],
];

/** "5 minutes ago", "yesterday", "just now" for an ISO timestamp, in the browser's language. */
export function timeAgo(isoDateTime) {
  const seconds = (Date.parse(isoDateTime) - Date.now()) / 1000;
  const format = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  for (const [unit, length] of RELATIVE_UNITS) {
    if (Math.abs(seconds) >= length) return format.format(Math.round(seconds / length), unit);
  }
  return 'just now';
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
