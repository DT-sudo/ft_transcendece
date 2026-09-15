import { useMemo } from 'react';

import { addDays, addMonths, monthMatrix, navigateWith, weekdayLabels } from '../app/dates.js';
import { t } from '../i18n/index.js';
import { ChevronLeft, ChevronRight } from './Icons.jsx';

/** Previous / Today / Next: reloads the page on the neighbouring month, or week when `view` is "week" (`?date=`). */
export function CalendarNav({ anchorISO, todayISO, view = 'month' }) {
  const step = (direction) =>
    navigateWith({ date: view === 'week' ? addDays(anchorISO, 7 * direction) : addMonths(anchorISO, direction) });

  return (
    <div className="flex items-center gap-2">
      {/* In RTL the row mirrors, so "previous" sits on the right and its chevron flips to point there. */}
      <button
        className="btn btn-outline btn-icon"
        type="button"
        onClick={() => step(-1)}
        aria-label={view === 'week' ? t('calendar.previousWeek') : t('calendar.previousMonth')}
      >
        <ChevronLeft className="rtl:-scale-x-100" />
      </button>
      <button className="btn btn-outline btn-sm" type="button" onClick={() => navigateWith({ date: todayISO })}>
        {t('calendar.today')}
      </button>
      <button
        className="btn btn-outline btn-icon"
        type="button"
        onClick={() => step(1)}
        aria-label={view === 'week' ? t('calendar.nextWeek') : t('calendar.nextMonth')}
      >
        <ChevronRight className="rtl:-scale-x-100" />
      </button>
    </div>
  );
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
        >
          <div className="calendar-date">{day.dayNumber}</div>
          {renderDay(day)}
        </div>
      ))}
    </div>
  );
}
