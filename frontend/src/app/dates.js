export const WEEKDAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export const pad2 = (value) => String(value).padStart(2, '0');

export function toISODate(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function dateFromISO(iso) {
  const cleaned = String(iso || '').trim();
  if (!cleaned) return null;

  const date = new Date(`${cleaned}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function addDays(iso, days) {
  const date = dateFromISO(iso);
  if (!date) return iso;

  date.setDate(date.getDate() + days);
  return toISODate(date);
}

export function addMonths(iso, months) {
  const date = dateFromISO(iso);
  if (!date) return iso;

  date.setMonth(date.getMonth() + months);
  return toISODate(date);
}

/** The 6x7 day matrix a month view paints, starting on Sunday. */
export function monthMatrix(anchorISO, todayISO) {
  const anchor = dateFromISO(anchorISO) || new Date();
  const month = anchor.getMonth();
  const firstOfMonth = new Date(anchor.getFullYear(), month, 1);

  const gridStart = new Date(firstOfMonth);
  gridStart.setDate(1 - firstOfMonth.getDay());

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    const iso = toISODate(date);

    return {
      date,
      iso,
      dayNumber: date.getDate(),
      inMonth: date.getMonth() === month,
      isToday: iso === todayISO,
    };
  });
}

export function weekDays(startISO) {
  const start = dateFromISO(startISO) || new Date();

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);

    return {
      date,
      iso: toISODate(date),
      label: date.toLocaleDateString(undefined, { weekday: 'short' }),
      dayNumber: date.getDate(),
    };
  });
}

export function parseTimeToMinutes(value) {
  const [hours, minutes] = String(value || '00:00').split(':').slice(0, 2).map(Number);
  return (Number.isFinite(hours) ? hours : 0) * 60 + (Number.isFinite(minutes) ? minutes : 0);
}

export function shiftDurationMinutes(shift) {
  return Math.max(0, parseTimeToMinutes(shift?.end_time) - parseTimeToMinutes(shift?.start_time));
}

/** "8h", "7h 30m", "45m". */
export function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return [hours && `${hours}h`, (rest || !hours) && `${rest}m`].filter(Boolean).join(' ');
}

/** "Sat, 19 Sept" or, with the year, "Sat, 19 Sept 2026". */
export function formatDate(iso, { year = true } = {}) {
  const date = dateFromISO(iso);
  if (!date) return String(iso || '');
  return date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: year ? 'numeric' : undefined });
}

/** Merge query parameters into the current URL and reload the page. */
export function navigateWith(params) {
  const url = new URL(window.location.href);

  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      url.searchParams.delete(key);
      value.forEach((item) => url.searchParams.append(key, item));
    } else if (value == null || value === '') {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, value);
    }
  }

  window.location.assign(`${url.pathname}?${url.searchParams.toString()}`);
}
