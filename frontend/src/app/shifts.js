import { parseTimeToMinutes, shiftDurationMinutes } from './dates.js';

// ── Positions & people ──────────────────────────────────────────────────────

/**
 * Chip colours are derived from the position id rather than stored, so a new
 * position is immediately distinguishable without a migration.
 */
export function positionPalette(positionId) {
  const hue = (parseInt(positionId, 10) * 47) % 360;
  return {
    '--position-bg': `hsl(${hue} 80% 92%)`,
    '--position-border': `hsl(${hue} 70% 45%)`,
    '--position-fg': `hsl(${hue} 60% 20%)`,
  };
}

export function initialsFromName(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'E';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

// ── Availability: Map of employee id (string) -> Set of ISO dates ───────────
// Seeded from the manager page payload and kept current by live
// `unavailability.changed` events.

export function availabilityFromPayload(payload) {
  return new Map(Object.entries(payload).map(([id, days]) => [id, new Set(days)]));
}

export function withAvailabilityChange(availability, { employeeId, date, unavailable }) {
  const days = new Set(availability.get(String(employeeId)));
  if (unavailable) days.add(date);
  else days.delete(date);
  return new Map(availability).set(String(employeeId), days);
}

export function isUnavailable(availability, employeeId, date) {
  return Boolean(date) && Boolean(availability.get(String(employeeId))?.has(date));
}

export function unavailableDaysBetween(availability, employeeId, start, end) {
  return [...(availability.get(String(employeeId)) || [])].filter((day) => day >= start && day <= end).sort();
}

// ── Calendar layout ─────────────────────────────────────────────────────────

export function groupShiftsByDate(shifts) {
  const byDate = new Map();
  for (const shift of shifts) {
    if (!byDate.has(shift.date)) byDate.set(shift.date, []);
    byDate.get(shift.date).push(shift);
  }
  for (const list of byDate.values()) {
    list.sort(
      (a, b) =>
        parseTimeToMinutes(a.start_time) - parseTimeToMinutes(b.start_time) ||
        parseTimeToMinutes(a.end_time) - parseTimeToMinutes(b.end_time) ||
        a.id - b.id,
    );
  }
  return byDate;
}

/**
 * Greedy lane placement: each shift drops into the first lane whose previous
 * shift has ended, and a new lane is allocated only when none is free.
 */
export function computeLaneLayout(shifts) {
  const laneEnds = [];
  const laneById = new Map();

  for (const shift of shifts) {
    const start = parseTimeToMinutes(shift.start_time);
    const end = parseTimeToMinutes(shift.end_time);
    let lane = laneEnds.findIndex((laneEnd) => start >= laneEnd);
    if (lane === -1) lane = laneEnds.push(end) - 1;
    else laneEnds[lane] = end;
    laneById.set(String(shift.id), lane);
  }

  return { laneById, laneCount: Math.max(1, laneEnds.length) };
}

const LANE_GAP_PX = 4;
const MINUTES_PER_DAY = 24 * 60;

/** Absolute position of a chip inside a day column that spans the full 24 hours. */
export function timedChipStyle(shift, laneIndex, laneCount) {
  const widthPct = 100 / laneCount;
  return {
    top: `${(parseTimeToMinutes(shift.start_time) / MINUTES_PER_DAY) * 100}%`,
    height: `max(18px, ${(shiftDurationMinutes(shift) / MINUTES_PER_DAY) * 100}%)`,
    left: `calc(${laneIndex * widthPct}% + ${LANE_GAP_PX}px)`,
    width: `calc(${widthPct}% - ${LANE_GAP_PX * 2}px)`,
  };
}

/** Shift ids and total scheduled minutes per employee for the visible period. */
export function employeePeriodStats(shifts) {
  const shiftIdsByEmployee = new Map();
  const minutesByEmployee = new Map();

  for (const shift of shifts) {
    for (const rawId of shift.assigned_employee_ids) {
      const employeeId = String(rawId);
      if (!shiftIdsByEmployee.has(employeeId)) shiftIdsByEmployee.set(employeeId, new Set());
      shiftIdsByEmployee.get(employeeId).add(String(shift.id));
      minutesByEmployee.set(employeeId, (minutesByEmployee.get(employeeId) || 0) + shiftDurationMinutes(shift));
    }
  }

  return { shiftIdsByEmployee, minutesByEmployee };
}
