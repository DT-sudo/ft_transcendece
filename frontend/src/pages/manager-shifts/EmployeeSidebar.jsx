import { formatDate } from '../../app/dates.js';
import { initialsFromName, positionPalette, unavailableDaysBetween } from '../../app/shifts.js';

const MAX_LISTED_DAYS = 3;

function formatDayList(days) {
  const listed = days.slice(0, MAX_LISTED_DAYS).map((day) => formatDate(day, { year: false })).join(', ');
  const rest = days.length - MAX_LISTED_DAYS;
  return rest > 0 ? `${listed} +${rest}` : listed;
}

/** Team list with each employee's unavailable days in the visible month, updated live. */
export function EmployeeSidebar({ employees, availability, periodStart, periodEnd, flashedEmployeeId }) {
  return (
    <aside className="card calendar-fill mt-3" aria-label="Employees">
      <h3 className="card-title border-b border-border px-4 py-2.5">Employees</h3>

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
                {employee.position_id ? (
                  <span className="badge badge-outline position-color max-w-full truncate" style={positionPalette(employee.position_id)}>
                    {employee.position}
                  </span>
                ) : null}
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
