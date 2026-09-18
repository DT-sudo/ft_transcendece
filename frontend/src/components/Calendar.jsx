import { useMemo } from 'react';

import { addDays, addMonths, monthMatrix, navigateWith, weekdayLabels } from '../app/dates.js';
import { t } from '../i18n/index.js';
import { ChevronLeft, ChevronRight } from './Icons.jsx';

/**
 * A "previous" (`step` -1) or "next" (`step` 1) chevron button. In RTL the row mirrors, so
 * "previous" sits on the right and its chevron flips to point there.
 */
export function StepButton({ step, label, onClick, disabled = false }) {
  const Chevron = step < 0 ? ChevronLeft : ChevronRight;
  return (
    <button className="btn btn-outline btn-icon" type="button" aria-label={label} disabled={disabled} onClick={onClick}>
      <Chevron className="rtl:-scale-x-100" />
    </button>
  );
}

/** Previous / Today / Next: reloads the page on the neighbouring month, or week when `view` is "week" (`?date=`). */
export function CalendarNav({ anchorISO, todayISO, view = 'month' }) {
  const week = view === 'week';
  const go = (step) => () => navigateWith({ date: week ? addDays(anchorISO, 7 * step) : addMonths(anchorISO, step) });

  return (
    <div className="flex items-center gap-2">
      <StepButton step={-1} label={week ? t('calendar.previousWeek') : t('calendar.previousMonth')} onClick={go(-1)} />
      <button className="btn btn-outline btn-sm" type="button" onClick={() => navigateWith({ date: todayISO })}>
        {t('calendar.today')}
      </button>
      <StepButton step={1} label={week ? t('calendar.nextWeek') : t('calendar.nextMonth')} onClick={go(1)} />
    </div>
  );
}

/** The bar above a calendar: `start` controls, the period it shows in the middle, `end` controls. */
export function CalendarToolbar({ period, start = null, end = null }) {
  return (
    <div className="card page-toolbar-card">
      <div className="shifts-toolbar">
        <div className="shifts-toolbar-left flex min-w-0 flex-wrap items-center gap-3 justify-self-start">{start}</div>
        <div className="shifts-toolbar-center min-w-0 justify-self-center">
          <div className="calendar-period">{period}</div>
        </div>
        <div className="shifts-toolbar-right flex min-w-0 flex-wrap items-center justify-end gap-3 justify-self-end">{end}</div>
      </div>
    </div>
  );
}

// A day's scrollbar shows while it scrolls, and fades this long after it stops.
const SCROLLBAR_MS = 800;
const scrollbarTimers = new WeakMap();

function showScrollbarWhileScrolling(event) {
  const cell = event.currentTarget;
  cell.classList.add('calendar-cell-scrolling');
  clearTimeout(scrollbarTimers.get(cell));
  scrollbarTimers.set(cell, setTimeout(() => cell.classList.remove('calendar-cell-scrolling'), SCROLLBAR_MS));
}

/** Six-week month grid shared by the manager and employee calendars. */
export function MonthCalendar({ anchorISO, todayISO, ariaLabel, dayClassName, renderDay, onDayClick }) {
  const days = useMemo(() => monthMatrix(anchorISO, todayISO), [anchorISO, todayISO]);

  return (
    <div className="calendar-grid" aria-label={ariaLabel}>
      {weekdayLabels().map((label) => (
        <div className="calendar-header-cell" key={label}>
          {label}
        </div>
      ))}

      {days.map((day) => (
        <div
          key={day.iso}
          className={`calendar-cell ${day.isToday ? 'calendar-cell-today' : ''} ${day.inMonth ? '' : 'calendar-cell-other-month'} ${dayClassName?.(day) || ''}`}
          onClick={() => onDayClick(day)}
          onScroll={showScrollbarWhileScrolling}
        >
          <div className="calendar-date">{day.dayNumber}</div>
          {renderDay(day)}
        </div>
      ))}
    </div>
  );
}
