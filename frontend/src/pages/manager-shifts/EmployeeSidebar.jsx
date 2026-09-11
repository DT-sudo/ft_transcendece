import { formatDate } from '../../app/dates.js';
import { initialsFromName, unavailableDaysBetween } from '../../app/shifts.js';

const MAX_LISTED_DAYS = 3;

const LIVE_LABELS = { connecting: 'Connecting…', live: 'Live', offline: 'Reconnecting…' };

function formatDayList(days) {
  const listed = days.slice(0, MAX_LISTED_DAYS).map((day) => formatDate(day, { year: false })).join(', ');
  const rest = days.length - MAX_LISTED_DAYS;
  return rest > 0 ? `${listed} +${rest}` : listed;
}

/** Team list with each employee's unavailable days in the visible month, updated live. */
export function EmployeeSidebar({ employees, availability, periodStart, periodEnd, flashedEmployeeId, liveStatus }) {
  return (
    <aside className="card manager-calendar-fill mt-3" aria-label="Employees">
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <h3 className="card-title">Employees</h3>
        <span className={`live-indicator live-indicator-${liveStatus}`} role="status" title="Employee availability updates in real time">
          <span className="live-indicator-dot" aria-hidden="true" />
          {LIVE_LABELS[liveStatus]}
        </span>
      </div>

      <ul className="flex flex-auto flex-col gap-2 overflow-auto p-3">
        {employees.map((employee) => {
          const days = unavailableDaysBetween(availability, employee.id, periodStart, periodEnd);
          const flashed = flashedEmployeeId === String(employee.id);
          return (
            <li key={employee.id} className={`employee-sidebar-item ${flashed ? 'employee-sidebar-item-updated' : ''}`}>
              <div className="avatar" aria-hidden="true">
                {initialsFromName(employee.name)}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">{employee.name}</div>
                <span className="badge badge-outline max-w-full truncate">{employee.position}</span>
                {days.length ? (
                  <div className="employee-sidebar-unavailable truncate">Unavailable: {formatDayList(days)}</div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
