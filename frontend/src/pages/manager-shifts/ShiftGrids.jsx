import { useLayoutEffect, useMemo, useRef, useState } from 'react';

import { formatDuration, navigateWith, pad2, shiftDurationMinutes, weekDays } from '../../app/dates.js';
import { computeLaneLayout, groupShiftsByDate, positionPalette, timedChipStyle } from '../../app/shifts.js';
import { MonthCalendar } from '../../components/Calendar.jsx';
import { t, useLanguage } from '../../i18n/index.js';

// `editors` (below) maps a shift id to the names of the other managers editing it.

/** The button both chip views share. Drafts stay neutral; published shifts take their position's colour. */
function ChipButton({ shift, editors, highlighted, variant, style, onSelect, children }) {
  const isDraft = shift.status === 'draft';
  const className = [
    'shift-chip',
    variant,
    shift.is_past ? 'shift-chip-past' : 'shift-chip-future',
    isDraft ? 'shift-chip-draft' : 'position-color',
    highlighted ? 'shift-chip-highlight' : '',
  ].join(' ');

  return (
    <button
      type="button"
      className={className}
      style={{ ...(isDraft ? null : positionPalette(shift.position_id)), ...style }}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(shift.id);
      }}
      title={`${shift.position} ${shift.start_time}-${shift.end_time}${editors ? ` (${t('shifts.editing', { names: editors.join(', ') })})` : ''}`}
    >
      {children}
    </button>
  );
}

/** "2/3" staffed, marked ✎ while another manager edits the shift. */
const Staffing = ({ shift, editors, className }) => (
  <span className={className}>
    {editors ? <span aria-label={t('shifts.editing', { names: editors.join(', ') })}>✎ </span> : null}
    {shift.assigned_employee_ids.length}/{shift.capacity}
  </span>
);

/** Month view: one compact row per shift that sheds detail as the cell narrows. */
function ShiftChip({ shift, editors, ...rest }) {
  return (
    <ChipButton shift={shift} editors={editors} variant="month-shift-chip" {...rest}>
      <span className="flex min-w-0 items-center justify-between gap-1.5">
        <span className="inline-flex min-w-0 flex-auto items-center gap-1 overflow-hidden">
          <span className="shift-chip-truncate text-[0.7rem] font-semibold">{shift.position}</span>
          <span className="month-shift-sep shrink-0 opacity-75">•</span>
          <span className="month-shift-time shift-chip-truncate text-[0.7rem] opacity-90">
            {shift.start_time}-{shift.end_time}
          </span>
        </span>
        <Staffing shift={shift} editors={editors} className="month-shift-qty shrink-0 text-[0.7rem] font-bold" />
      </span>
    </ChipButton>
  );
}

/** Week view: a block placed and sized by its times (`style` from `timedChipStyle`). */
function WeekShiftChip({ shift, editors, ...rest }) {
  return (
    <ChipButton shift={shift} editors={editors} variant="shift-chip-timed" {...rest}>
      <span className="flex min-w-0 items-center justify-between gap-2">
        <span className="shift-chip-truncate font-semibold">{shift.position}</span>
        <Staffing shift={shift} editors={editors} className="shrink-0 font-bold" />
      </span>
      <span className="mt-1 block shift-chip-truncate">
        {shift.start_time}-{shift.end_time}
      </span>
      <span className="mt-0.5 block text-[0.6875rem] whitespace-nowrap opacity-85">
        {formatDuration(shiftDurationMinutes(shift))}
      </span>
    </ChipButton>
  );
}

export function MonthGrid({ anchorISO, todayISO, shifts, editors, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);

  return (
    <MonthCalendar
      anchorISO={anchorISO}
      todayISO={todayISO}
      ariaLabel={t('shifts.monthSchedule')}
      onDayClick={(day) => (day.inMonth ? onCreateSlot(day.iso) : navigateWith({ date: day.iso }))}
      renderDay={(day) => {
        const dayShifts = byDate.get(day.iso);
        if (!dayShifts) return null;

        return (
          <div className="month-cell-shifts">
            {dayShifts.map((shift) => (
              <ShiftChip
                key={shift.id}
                shift={shift}
                editors={editors[shift.id]}
                highlighted={highlightedShiftIds.has(shift.id)}
                onSelect={onSelectShift}
              />
            ))}
          </div>
        );
      }}
    />
  );
}

const DEFAULT_HOUR_HEIGHT_PX = 56;
const HOURS = Array.from({ length: 24 }, (_, hour) => `${pad2(hour)}:00`);

/** Seven day columns over 24 hour rows. Overlapping shifts share a day in lanes, and busy days get wider. */
export function WeekGrid({ startISO, todayISO, shifts, editors, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const gridRef = useRef(null);
  const [hourHeight, setHourHeight] = useState(DEFAULT_HOUR_HEIGHT_PX);

  const language = useLanguage();
  // The day labels are written in the page's language.
  const days = useMemo(() => weekDays(startISO), [startISO, language]);
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);
  const lanesByDate = useMemo(
    () => new Map(days.map(({ iso }) => [iso, computeLaneLayout(byDate.get(iso) || [])])),
    [days, byDate],
  );

  // Every two lanes widen the day by one column. Days fill the card and scroll sideways only when they can't fit.
  const gridTemplateColumns = useMemo(() => {
    const widths = days.map(({ iso }) => {
      const span = Math.ceil(lanesByDate.get(iso).laneCount / 2);
      return `minmax(calc(${span} * var(--week-day-col-width)), ${span}fr)`;
    });
    return `var(--week-hour-label-width) ${widths.join(' ')}`;
  }, [days, lanesByDate]);

  // Chips are positioned in pixels, so measure the hour height the stylesheet produced.
  useLayoutEffect(() => {
    const cell = gridRef.current?.querySelector('.week-cell');
    if (cell) setHourHeight(cell.getBoundingClientRect().height || DEFAULT_HOUR_HEIGHT_PX);
  }, [gridTemplateColumns]);

  return (
    <div ref={gridRef} className="calendar-grid calendar-grid-week" style={{ gridTemplateColumns }} aria-label={t('shifts.weekSchedule')}>
      <div className="calendar-header-cell week-corner" style={{ gridColumn: 1, gridRow: 1 }} />

      {days.map((day, index) => (
        <div key={day.iso} className="calendar-header-cell" style={{ gridColumn: index + 2, gridRow: 1 }}>
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
              key={day.iso}
              className={`week-cell ${day.iso === todayISO ? 'calendar-cell-today' : ''}`}
              style={{ gridColumn: dayIndex + 2, gridRow: hourIndex + 2 }}
              onClick={() => onCreateSlot(day.iso, hour)}
            />
          ))}
        </div>
      ))}

      {days.map((day, dayIndex) => {
        const { laneById, laneCount } = lanesByDate.get(day.iso);
        return (
          <div key={`layer-${day.iso}`} className="week-shifts-layer" style={{ gridColumn: dayIndex + 2, gridRow: '2 / -1' }}>
            {(byDate.get(day.iso) || []).map((shift) => (
              <WeekShiftChip
                key={shift.id}
                shift={shift}
                editors={editors[shift.id]}
                highlighted={highlightedShiftIds.has(shift.id)}
                onSelect={onSelectShift}
                style={timedChipStyle(shift, laneById.get(shift.id), laneCount, hourHeight)}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}
