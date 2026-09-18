import { positionPalette } from '../../app/shifts.js';
import { Avatar } from '../../components/Avatar.jsx';
import { t } from '../../i18n/index.js';

/**
 * The team beside the calendar: who works here and in what position. Clicking a row
 * outlines that person's shifts in the grid; clicking again clears it.
 *
 * Days off are not listed here. The calendar itself is where a day is read, and the shift
 * form marks anyone unavailable on the day being filled - a second copy in the margin only
 * competed with them.
 */
export function EmployeeSidebar({ employees, flashedEmployeeId, highlightedEmployeeId, onToggleEmployee }) {
  return (
    <aside className="card calendar-fill mt-3" aria-label={t('shifts.employees')}>
      <h3 className="card-title border-b border-border px-4 py-2.5">{t('shifts.employees')}</h3>

      <ul className="flex flex-auto flex-col gap-2 overflow-auto p-3">
        {employees.map((employee) => {
          const flashed = flashedEmployeeId === String(employee.id);
          const active = highlightedEmployeeId === employee.id;
          return (
            <li key={employee.id}>
              <button
                type="button"
                aria-pressed={active}
                title={t('shifts.highlightShifts', { name: employee.name })}
                className={`employee-sidebar-item ${active ? 'employee-sidebar-item-active' : ''} ${flashed ? 'employee-sidebar-item-updated' : ''}`}
                onClick={() => onToggleEmployee(employee.id)}
              >
                <Avatar name={employee.name} />
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{employee.name}</div>
                  {employee.position_id ? (
                    <span className="badge badge-outline position-color max-w-full truncate" style={positionPalette(employee.position_id)}>
                      {employee.position}
                    </span>
                  ) : null}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
