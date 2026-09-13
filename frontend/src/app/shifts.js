// ── Status ──────────────────────────────────────────────────────────────────

export const STATUS_OPTIONS = [
  { id: 'draft', name: 'Draft' },
  { id: 'published', name: 'Published' },
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

// ── People ──────────────────────────────────────────────────────────────────

/** "Maya Rossi" -> "MR", "Maya" -> "MA". */
export function initialsFromName(name) {
  const [first, second] = name.trim().split(/\s+/);
  return (second ? first[0] + second[0] : first.slice(0, 2)).toUpperCase();
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
