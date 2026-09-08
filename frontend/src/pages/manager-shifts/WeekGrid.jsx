import { useLayoutEffect, useMemo, useRef, useState } from 'react';

import { pad2, weekDays } from '../../app/dates.js';
import { computeLaneLayout, groupShiftsByDate, timedChipStyle } from '../../app/shifts.js';
import { WeekShiftChip } from './ShiftChip.jsx';

const DEFAULT_HOUR_HEIGHT_PX = 56;
const HOURS = Array.from({ length: 24 }, (_, hour) => `${pad2(hour)}:00`);

export function WeekGrid({ startISO, todayISO, shifts, highlightedShiftIds, onSelectShift, onCreateSlot }) {
  const gridRef = useRef(null);
  const [hourHeight, setHourHeight] = useState(DEFAULT_HOUR_HEIGHT_PX);

  const days = useMemo(() => weekDays(startISO), [startISO]);
  const byDate = useMemo(() => groupShiftsByDate(shifts), [shifts]);
  const lanesByDate = useMemo(() => {
    const lanes = new Map();
    for (const { iso } of days) lanes.set(iso, computeLaneLayout(byDate.get(iso) || []));
    return lanes;
  }, [days, byDate]);

  // Days with many overlapping shifts get proportionally wider columns.
  const gridTemplateColumns = useMemo(() => {
    const widths = days.map(({ iso }) => {
      const laneCount = lanesByDate.get(iso)?.laneCount || 1;
      const span = Math.max(1, Math.ceil(laneCount / 2));
      return span === 1 ? 'var(--week-day-col-width)' : `calc(${span} * var(--week-day-col-width))`;
    });
    return `var(--week-hour-label-width) ${widths.join(' ')}`;
  }, [days, lanesByDate]);

  useLayoutEffect(() => {
    const cell = gridRef.current?.querySelector('.week-cell');
    if (cell) setHourHeight(cell.getBoundingClientRect().height || DEFAULT_HOUR_HEIGHT_PX);
  }, [gridTemplateColumns]);

  return (
    <div
      ref={gridRef}
      className="calendar-grid calendar-grid-week"
      style={{ gridTemplateColumns }}
      aria-label="Week calendar"
    >
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
          <div
            key={`layer-${day.iso}`}
            className="week-shifts-layer"
            style={{ gridColumn: dayIndex + 2, gridRow: '2 / -1' }}
          >
            {(byDate.get(day.iso) || []).map((shift) => (
              <WeekShiftChip
                key={shift.id}
                shift={shift}
                highlighted={highlightedShiftIds.has(String(shift.id))}
                onSelect={onSelectShift}
                style={timedChipStyle(
                  shift,
                  lanes?.laneById.get(String(shift.id)) ?? 0,
                  lanes?.laneCount ?? 1,
                  hourHeight,
                )}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}
