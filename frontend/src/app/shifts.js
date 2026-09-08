import { parseTimeToMinutes, shiftDurationMinutes } from './dates.js';

export function groupShiftsByDate(shifts) {
  const byDate = new Map();

  for (const shift of shifts || []) {
    if (!shift?.date) continue;
    if (!byDate.has(shift.date)) byDate.set(shift.date, []);
    byDate.get(shift.date).push(shift);
  }

  for (const list of byDate.values()) {
    list.sort(
      (a, b) =>
        parseTimeToMinutes(a.start_time) - parseTimeToMinutes(b.start_time) ||
        parseTimeToMinutes(a.end_time) - parseTimeToMinutes(b.end_time) ||
        String(a.id).localeCompare(String(b.id)),
    );
  }

  return byDate;
}

/**
 * Greedy lane placement: each shift drops into the first lane whose previous
 * shift has ended, and a new lane is allocated only when none is free.
 */
export function computeLaneLayout(shifts) {
  const items = (shifts || [])
    .map((shift) => ({
      id: String(shift.id),
      start: parseTimeToMinutes(shift.start_time),
      end: parseTimeToMinutes(shift.end_time),
    }))
    .sort((a, b) => a.start - b.start || a.end - b.end || a.id.localeCompare(b.id));

  const laneEnds = [];
  const laneById = new Map();

  for (const item of items) {
    let laneIndex = laneEnds.findIndex((end) => item.start >= end);
    if (laneIndex === -1) {
      laneIndex = laneEnds.length;
      laneEnds.push(item.end);
    } else {
      laneEnds[laneIndex] = item.end;
    }
    laneById.set(item.id, laneIndex);
  }

  return { laneById, laneCount: Math.max(1, laneEnds.length) };
}

const LANE_GAP_PX = 4;

export function timedChipStyle(shift, laneIndex, laneCount, hourHeightPx) {
  const start = parseTimeToMinutes(shift.start_time);
  const lanes = Math.max(1, laneCount || 1);
  const lane = Math.min(Math.max(0, laneIndex || 0), lanes - 1);
  const widthPct = 100 / lanes;

  return {
    top: `${(start / 60) * hourHeightPx}px`,
    height: `${Math.max(18, (shiftDurationMinutes(shift) / 60) * hourHeightPx)}px`,
    left: `calc(${lane * widthPct}% + ${LANE_GAP_PX}px)`,
    width: `calc(${widthPct}% - ${LANE_GAP_PX * 2}px)`,
  };
}

/** Shift ids and total scheduled minutes per employee for the visible period. */
export function employeePeriodStats(shifts) {
  const shiftIdsByEmployee = new Map();
  const minutesByEmployee = new Map();

  for (const shift of shifts || []) {
    const shiftId = String(shift?.id ?? '');
    if (!shiftId) continue;

    const duration = shiftDurationMinutes(shift);
    for (const rawId of shift.assigned_employee_ids || []) {
      const employeeId = String(rawId ?? '');
      if (!employeeId) continue;

      if (!shiftIdsByEmployee.has(employeeId)) shiftIdsByEmployee.set(employeeId, new Set());
      shiftIdsByEmployee.get(employeeId).add(shiftId);
      minutesByEmployee.set(employeeId, (minutesByEmployee.get(employeeId) || 0) + duration);
    }
  }

  return { shiftIdsByEmployee, minutesByEmployee };
}
