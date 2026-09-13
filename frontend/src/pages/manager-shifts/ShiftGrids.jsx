import { useMemo } from 'react';

import { navigateWith } from '../../app/dates.js';
import { groupShiftsByDate, positionPalette } from '../../app/shifts.js';
import { MonthCalendar } from '../../components/Calendar.jsx';

/** One compact row per shift that sheds detail as the cell narrows. Drafts stay neutral; published shifts take their position's colour. */
function ShiftChip({ shift, onSelect }) {
  const isDraft = shift.status === 'draft';
  const classes = [
    'shift-chip month-shift-chip',
    shift.is_past ? 'shift-chip-past' : 'shift-chip-future',
    isDraft ? 'shift-chip-draft' : 'position-color',
  ].join(' ');

  return (
    <button
      type="button"
      className={classes}
      style={isDraft ? undefined : positionPalette(shift.position_id)}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(shift.id);
      }}
      title={`${shift.position} ${shift.start_time}-${shift.end_time}`}
    >
      <span className="flex min-w-0 items-center justify-between gap-1.5">
        <span className="inline-flex min-w-0 flex-auto items-center gap-1 overflow-hidden">
          <span className="shift-chip-truncate text-[0.7rem] font-semibold">{shift.position}</span>
          <span className="month-shift-sep shrink-0 opacity-75">•</span>
          <span className="month-shift-time shift-chip-truncate text-[0.7rem] opacity-90">
            {shift.start_time}-{shift.end_time}
          </span>
        </span>
        <span className="month-shift-qty shrink-0 text-[0.7rem] font-bold">
          {shift.assigned_employee_ids.length}/{shift.capacity}
        </span>
      </span>
    </button>
  );
}

export function MonthGrid({ anchorISO, todayISO, shifts, onSelectShift, onCreateSlot }) {
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);

  return (
    <MonthCalendar
      anchorISO={anchorISO}
      todayISO={todayISO}
      ariaLabel="Month schedule"
      onDayClick={(day) => (day.inMonth ? onCreateSlot(day.iso) : navigateWith({ date: day.iso }))}
      renderDay={(day) => {
        const dayShifts = byDate.get(day.iso);
        if (!dayShifts) return null;

        return (
          <div className="month-cell-shifts">
            {dayShifts.map((shift) => (
              <ShiftChip key={shift.id} shift={shift} onSelect={onSelectShift} />
            ))}
          </div>
        );
      }}
    />
  );
}
