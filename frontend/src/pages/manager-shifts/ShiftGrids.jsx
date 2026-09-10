import { useMemo } from 'react';

import { formatDuration, navigateWith, pad2, shiftDurationMinutes, weekDays } from '../../app/dates.js';
import { computeLaneLayout, groupShiftsByDate, positionPalette, timedChipStyle } from '../../app/shifts.js';
import { MonthCalendar } from '../../components/Calendar.jsx';

// ── Chips ───────────────────────────────────────────────────────────────────

function chipClasses(shift, highlighted, extra) {
  return [
    'shift-chip',
    shift.is_past ? 'shift-chip-past' : 'shift-chip-future',
    shift.status === 'draft' ? 'shift-chip-draft' : 'shift-chip-published shift-chip-position',
    highlighted ? 'shift-chip-highlight' : '',
    extra,
  ].join(' ');
}

// Draft chips keep the neutral dashed look instead of a position colour.
const chipStyle = (shift, style) => ({ ...(shift.status === 'draft' ? null : positionPalette(shift.position_id)), ...style });

/** Week view: absolutely positioned block sized to the shift's duration. */
function WeekShiftChip({ shift, style, highlighted, onSelect }) {
  return (
    <button
      type="button"
      className={chipClasses(shift, highlighted, 'shift-chip-timed')}
      style={chipStyle(shift, style)}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(shift.id);
      }}
    >
      <span className="flex min-w-0 items-center justify-between gap-2">
        <span className="shift-chip-truncate font-semibold" title={shift.position}>
          {shift.position}
        </span>
        <span className="shift-chip-qty shrink-0 font-bold">
          {shift.assigned_count}/{shift.capacity}
        </span>
      </span>
      <span className="shift-chip-time mt-1 block shift-chip-truncate">
        {shift.start_time}-{shift.end_time}
      </span>
      <span className="shift-chip-duration mt-0.5 block text-[0.6875rem] whitespace-nowrap opacity-85">
        {formatDuration(shiftDurationMinutes(shift))}
      </span>
    </button>
  );
}

/** Month view: single compact row that sheds detail as the cell narrows. */
function MonthShiftChip({ shift, highlighted, onSelect }) {
  return (
    <button
      type="button"
      className={chipClasses(shift, highlighted, 'month-shift-chip')}
      style={chipStyle(shift)}
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
          {shift.assigned_count}/{shift.capacity}
        </span>
      </span>
    </button>
  );
}

// ── Grids ───────────────────────────────────────────────────────────────────

const HOURS = Array.from({ length: 24 }, (_, hour) => `${pad2(hour)}:00`);

export function WeekGrid({ startISO, todayISO, shifts, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const days = useMemo(() => weekDays(startISO), [startISO]);
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);
  const lanesByDate = useMemo(
    () => new Map(days.map(({ iso }) => [iso, computeLaneLayout(byDate.get(iso) || [])])),
    [days, byDate],
  );

  // Days with many overlapping shifts get proportionally wider columns.
  const gridTemplateColumns = useMemo(() => {
    const widths = days.map(({ iso }) => {
      const span = Math.max(1, Math.ceil(lanesByDate.get(iso).laneCount / 2));
      return span === 1 ? 'var(--week-day-col-width)' : `calc(${span} * var(--week-day-col-width))`;
    });
    return `var(--week-hour-label-width) ${widths.join(' ')}`;
  }, [days, lanesByDate]);

  return (
    <div className="calendar-grid calendar-grid-week" style={{ gridTemplateColumns }} aria-label="Week calendar">
      <div className="week-corner" style={{ gridColumn: 1, gridRow: 1 }} />

      {days.map((day, index) => (
        <div key={day.iso} className="week-day-header" style={{ gridColumn: index + 2, gridRow: 1 }}>
          {day.label} {day.dayNumber}
        </div>
      ))}

      {HOURS.map((hour, hourIndex) => (
        <div className="contents" key={hour}>
          <div className="week-hour-label" style={{ gridColumn: 1, gridRow: hourIndex + 2 }}>
            {hour}
          </div>
          {days.map((day, dayIndex) => (
            <div
              key={`${day.iso}-${hour}`}
              className={`week-cell ${day.iso === todayISO ? 'calendar-cell-today' : ''}`}
              style={{ gridColumn: dayIndex + 2, gridRow: hourIndex + 2 }}
              onClick={() => onCreateSlot(day.iso, hour)}
            />
          ))}
        </div>
      ))}

      {days.map((day, dayIndex) => {
        const lanes = lanesByDate.get(day.iso);
        return (
          <div key={`layer-${day.iso}`} className="week-shifts-layer" style={{ gridColumn: dayIndex + 2, gridRow: '2 / -1' }}>
            {(byDate.get(day.iso) || []).map((shift) => (
              <WeekShiftChip
                key={shift.id}
                shift={shift}
                highlighted={highlightedShiftIds.has(String(shift.id))}
                onSelect={onSelectShift}
                style={timedChipStyle(shift, lanes.laneById.get(String(shift.id)), lanes.laneCount)}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}

export function MonthGrid({ anchorISO, todayISO, shifts, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);

  return (
    <MonthCalendar
      anchorISO={anchorISO}
      todayISO={todayISO}
      ariaLabel="Month schedule"
      onDayClick={(day) => (day.inMonth ? onCreateSlot(day.iso) : navigateWith({ view: 'month', date: day.iso }))}
      renderDay={(day) => {
        const dayShifts = byDate.get(day.iso);
        if (!dayShifts) return null;

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
