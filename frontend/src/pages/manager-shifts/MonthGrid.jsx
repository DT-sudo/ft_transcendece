import { useMemo } from 'react';

import { navigateWith } from '../../app/dates.js';
import { groupShiftsByDate } from '../../app/shifts.js';
import { MonthCalendar } from '../../components/Calendar.jsx';
import { MonthShiftChip } from './ShiftChip.jsx';

export function MonthGrid({ anchorISO, todayISO, shifts, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);

  return (
    <MonthCalendar
      anchorISO={anchorISO}
      todayISO={todayISO}
      ariaLabel="Month schedule"
      onDayClick={(day) => {
        if (!day.inMonth) {
          navigateWith({ view: 'month', date: day.iso });
          return;
        }
        onCreateSlot(day.iso);
      }}
      renderDay={(day) => {
        const dayShifts = byDate.get(day.iso) || [];
        if (!dayShifts.length) return null;

        return (
          <div className="month-cell-shifts">
            {dayShifts.map((shift) => (
              <MonthShiftChip
                key={shift.id}
                shift={shift}
                highlighted={highlightedShiftIds.has(String(shift.id))}
                onSelect={onSelectShift}
              />
            ))}
          </div>
        );
      }}
    />
  );
}
