import { formatDurationMinutes, shiftDurationMinutes } from '../../app/dates.js';
import { positionPalette } from '../../app/positions.js';

function chipClasses(shift, { highlighted, extra = '' }) {
  return [
    'shift-chip',
    shift.is_past ? 'shift-chip-past' : 'shift-chip-future',
    shift.status === 'draft' ? 'shift-chip-draft' : 'shift-chip-published',
    shift.status === 'draft' ? '' : 'shift-chip-position',
    highlighted ? 'shift-chip-highlight' : '',
    extra,
  ]
    .filter(Boolean)
    .join(' ');
}

function chipStyle(shift, style) {
  // Draft chips keep the neutral dashed look instead of a position colour.
  const palette = shift.status === 'draft' ? null : positionPalette(shift.position_id);
  return { ...palette, ...style };
}

/** Week view: absolutely positioned block sized to the shift's duration. */
export function WeekShiftChip({ shift, style, highlighted, onSelect }) {
  const duration = formatDurationMinutes(shiftDurationMinutes(shift));

  return (
    <button
      type="button"
      className={chipClasses(shift, { highlighted, extra: 'shift-chip-timed' })}
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
        {duration}
      </span>
    </button>
  );
}

/** Month view: single compact row that sheds detail as the cell narrows. */
export function MonthShiftChip({ shift, highlighted, onSelect }) {
  return (
    <button
      type="button"
      className={chipClasses(shift, { highlighted, extra: 'month-shift-chip' })}
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
