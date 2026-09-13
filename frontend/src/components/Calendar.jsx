import { useMemo } from 'react';

import { WEEKDAY_LABELS, addMonths, monthMatrix, navigateWith } from '../app/dates.js';
import { ChevronLeft, ChevronRight } from './Icons.jsx';

/** Previous / Today / Next: reloads the page on the chosen month (`?date=`). */
export function CalendarNav({ anchorISO, todayISO }) {
  return (
    <div className="flex items-center gap-2">
      <button className="btn btn-outline btn-icon" type="button" onClick={() => navigateWith({ date: addMonths(anchorISO, -1) })} aria-label="Previous month">
        <ChevronLeft />
      </button>
      <button className="btn btn-outline btn-sm" type="button" onClick={() => navigateWith({ date: todayISO })}>
        Today
      </button>
      <button className="btn btn-outline btn-icon" type="button" onClick={() => navigateWith({ date: addMonths(anchorISO, 1) })} aria-label="Next month">
        <ChevronRight />
      </button>
    </div>
  );
}

/** Six-week month grid shared by the manager and employee calendars. */
export function MonthCalendar({ anchorISO, todayISO, ariaLabel, dayClassName, renderDay, onDayClick }) {
  const days = useMemo(() => monthMatrix(anchorISO, todayISO), [anchorISO, todayISO]);

  return (
    <div className="calendar-grid" aria-label={ariaLabel}>
      {WEEKDAY_LABELS.map((label) => (
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
