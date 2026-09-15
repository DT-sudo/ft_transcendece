import { t } from '../i18n/index.js';
import { minutesOf, shiftDurationMinutes } from './dates.js';

// ── Status ──────────────────────────────────────────────────────────────────

/** The two statuses as `{ id, name }` select options, named in the current language. */
export const statusOptions = () => [
  { id: 'draft', name: t('status.draft') },
  { id: 'published', name: t('status.published') },
];

// ── Positions ───────────────────────────────────────────────────────────────

/** Colour custom properties for `.position-color`, derived from the id so new positions need no setup. */
export function positionPalette(positionId) {
  const hue = (positionId * 47) % 360;
  return {
    '--position-bg': `hsl(${hue} 80% 92%)`,
    '--position-border': `hsl(${hue} 70% 45%)`,
    '--position-fg': `hsl(${hue} 60% 20%)`,
  };
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
  return availability.get(String(employeeId))?.has(date) ?? false;
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
  // "HH:MM" strings sort correctly as plain text.
  for (const list of byDate.values()) {
    list.sort((a, b) => a.start_time.localeCompare(b.start_time) || a.end_time.localeCompare(b.end_time) || a.id - b.id);
  }
  return byDate;
}

/**
 * Week view: overlapping shifts on one day sit side by side. Each shift (in start order,
 * as `groupShiftsByDate` returns them) takes the first lane that is free at its start.
 */
export function computeLaneLayout(shifts) {
  const laneEnds = [];
  const laneById = new Map();
  for (const shift of shifts) {
    const start = minutesOf(shift.start_time);
    let lane = laneEnds.findIndex((end) => start >= end);
    if (lane === -1) lane = laneEnds.length;
    laneEnds[lane] = minutesOf(shift.end_time);
    laneById.set(shift.id, lane);
  }
  return { laneById, laneCount: Math.max(1, laneEnds.length) };
}

const LANE_GAP_PX = 4;

/** Where a week-view chip goes: top and height from its times, inline start and width from its lane (mirrored in RTL). */
export function timedChipStyle(shift, lane, laneCount, hourHeightPx) {
  const width = 100 / laneCount;
  return {
    top: `${(minutesOf(shift.start_time) / 60) * hourHeightPx}px`,
    height: `${Math.max(18, (shiftDurationMinutes(shift) / 60) * hourHeightPx)}px`,
    insetInlineStart: `calc(${lane * width}% + ${LANE_GAP_PX}px)`,
    width: `calc(${width}% - ${LANE_GAP_PX * 2}px)`,
  };
}
