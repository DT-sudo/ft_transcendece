import { useMemo, useState } from 'react';

import { formatDate, formatDuration } from '../../app/dates.js';
import { initialsFromName, positionPalette, unavailableDaysBetween } from '../../app/shifts.js';

const UNASSIGNED = '__none__';
const MAX_LISTED_DAYS = 3;

const LIVE_LABELS = {
  connecting: 'Connecting…',
  live: 'Live',
  offline: 'Reconnecting…',
};

function matchesFilter(employee, filter) {
  if (!filter) return true;
  const positionId = employee.position_id;
  if (filter === UNASSIGNED) return positionId == null || String(positionId) === '';
  return String(positionId) === String(filter);
}

function formatDayList(days) {
  const listed = days.slice(0, MAX_LISTED_DAYS).map((day) => formatDate(day, { year: false })).join(', ');
  const rest = days.length - MAX_LISTED_DAYS;
  return rest > 0 ? `${listed} +${rest}` : listed;
}

function LiveIndicator({ status }) {
  return (
    <span
      className={`live-indicator live-indicator-${status}`}
      role="status"
      title="Employee availability updates in real time"
    >
      <span className="live-indicator-dot" aria-hidden="true" />
      {LIVE_LABELS[status]}
    </span>
  );
}

/** Team list for the visible period: scheduled hours, unavailable days and shift highlighting. */
export function EmployeeSidebar({
  employees,
  positions,
  minutesByEmployee,
  availability,
  periodStart,
  periodEnd,
  flashedEmployeeId,
  liveStatus,
  activeEmployeeId,
  onToggleEmployee,
}) {
  const [positionFilter, setPositionFilter] = useState('');

  const visible = useMemo(
    () =>
      employees
        .filter((employee) => matchesFilter(employee, positionFilter))
        .map((employee) => ({
          ...employee,
          key: String(employee.id ?? ''),
          displayName: String(employee.name || '') || 'Employee',
          minutes: minutesByEmployee.get(String(employee.id ?? '')) || 0,
          unavailableDays: unavailableDaysBetween(availability, employee.id, periodStart, periodEnd),
        }))
        .sort((a, b) => a.displayName.localeCompare(b.displayName) || a.key.localeCompare(b.key)),
    [employees, positionFilter, minutesByEmployee, availability, periodStart, periodEnd],
  );

  return (
    <aside className="card manager-calendar-fill mt-3" aria-label="Employees">
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <h3 className="card-title">Employees</h3>
        <LiveIndicator status={liveStatus} />
      </div>

      <div className="border-b border-border p-2">
        <label className="form-label mb-1 text-xs" htmlFor="employeeSidebarPosition">
          Position
        </label>
        <select
          id="employeeSidebarPosition"
          className="form-select py-1.5 pl-2.5 text-[0.8125rem]"
          value={positionFilter}
          onChange={(event) => setPositionFilter(event.target.value)}
        >
          <option value="">All positions</option>
          <option value={UNASSIGNED}>Unassigned</option>
          {positions.map((position) => (
            <option key={position.id} value={position.id}>
              {position.name}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-auto flex-col gap-2 overflow-auto p-3" role="list">
        {visible.length === 0 ? (
          <div className="p-3 text-sm text-muted-foreground">No employees found.</div>
        ) : (
          visible.map((employee) => {
            const active = String(activeEmployeeId || '') === employee.key;
            const flashed = flashedEmployeeId === employee.key;
            const unavailableText = employee.unavailableDays.length
              ? `Unavailable: ${formatDayList(employee.unavailableDays)}`
              : '';

            return (
              <button
                key={employee.key}
                type="button"
                role="listitem"
                aria-pressed={active}
                aria-label={`Highlight shifts for ${employee.displayName}${unavailableText ? `. ${unavailableText}` : ''}`}
                className={`employee-sidebar-item ${active ? 'employee-sidebar-item-active' : ''} ${
                  flashed ? 'employee-sidebar-item-updated' : ''
                }`}
                onClick={() => onToggleEmployee(employee.key)}
              >
                <div className="avatar" aria-hidden="true">
                  {initialsFromName(employee.displayName)}
                </div>

                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{employee.displayName}</div>
                  <div className="mt-0.5 flex items-center justify-between gap-2">
                    <span
                      className="badge badge-outline max-w-full truncate"
                      style={employee.position_id ? positionPalette(employee.position_id) : undefined}
                    >
                      {employee.position || 'Unassigned'}
                    </span>
                    {employee.minutes > 0 ? (
                      <span className="shrink-0 text-xs font-bold text-muted-foreground tabular-nums">
                        {formatDuration(employee.minutes)}
                      </span>
                    ) : null}
                  </div>
                  {unavailableText ? (
                    <div className="employee-sidebar-unavailable truncate">{unavailableText}</div>
                  ) : null}
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
