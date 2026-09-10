import { useMemo } from 'react';

import { WEEKDAY_LABELS, monthMatrix } from '../app/dates.js';
import { ChevronLeft, ChevronRight } from './Icons.jsx';

export function CalendarNav({ onPrev, onToday, onNext }) {
  return (
    <div className="flex items-center gap-2">
      <button className="btn btn-outline btn-icon" type="button" onClick={onPrev} aria-label="Previous period">
        <ChevronLeft />
      </button>
      <button className="btn btn-outline btn-sm" type="button" onClick={onToday}>
        Today
      </button>
      <button className="btn btn-outline btn-icon" type="button" onClick={onNext} aria-label="Next period">
        <ChevronRight />
      </button>
    </div>
  );
}

/** Six-week month grid shared by the manager and employee calendars. */
export function MonthCalendar({ anchorISO, todayISO, ariaLabel, dayClassName, renderDay, onDayClick }) {
  const days = useMemo(() => monthMatrix(anchorISO, todayISO), [anchorISO, todayISO]);

  return (
    <div className="calendar-grid calendar-grid-month" aria-label={ariaLabel}>
      {WEEKDAY_LABELS.map((label) => (
        <div className="calendar-header-cell" key={label}>
          {label}
        </div>
      ))}

      {days.map((day) => (
        <div
          key={day.iso}
          data-date={day.iso}
          className={[
            'calendar-cell',
            day.isToday ? 'calendar-cell-today' : '',
            day.inMonth ? '' : 'calendar-cell-other-month',
            dayClassName?.(day) || '',
          ]
            .filter(Boolean)
            .join(' ')}
          onClick={onDayClick ? () => onDayClick(day) : undefined}
        >
          <div className="calendar-date">{day.dayNumber}</div>
          {renderDay?.(day)}
        </div>
      ))}
    </div>
  );
}
