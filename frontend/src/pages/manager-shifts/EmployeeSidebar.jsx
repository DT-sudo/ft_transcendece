import { useMemo, useState } from 'react';

import { formatHours } from '../../app/dates.js';
import { initialsFromName, positionPalette } from '../../app/positions.js';

const UNASSIGNED = '__none__';

function matchesFilter(employee, filter) {
  if (!filter) return true;
  const positionId = employee.position_id;
  if (filter === UNASSIGNED) return positionId == null || String(positionId) === '';
  return String(positionId) === String(filter);
}

/** Team list for the visible period: scheduled hours plus shift highlighting. */
export function EmployeeSidebar({ employees, positions, minutesByEmployee, activeEmployeeId, onToggleEmployee }) {
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
        }))
        .sort((a, b) => a.displayName.localeCompare(b.displayName) || a.key.localeCompare(b.key)),
    [employees, positionFilter, minutesByEmployee],
  );

  return (
    <aside className="card manager-calendar-fill mt-3" aria-label="Employees">
      <div className="border-b border-border px-4 py-2.5">
        <h3 className="card-title">Employees</h3>
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
            return (
              <button
                key={employee.key}
                type="button"
                role="listitem"
                aria-pressed={active}
                aria-label={`Highlight shifts for ${employee.displayName}`}
                className={`employee-sidebar-item ${active ? 'employee-sidebar-item-active' : ''}`}
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
                        {formatHours(employee.minutes)}
                      </span>
                    ) : null}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
