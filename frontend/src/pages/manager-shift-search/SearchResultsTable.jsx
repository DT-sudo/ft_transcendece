import { formatDateDMY } from '../../app/dates.js';
import { ArrowUpDown } from '../../components/Icons.jsx';

const SORTABLE_COLUMNS = [
  { key: 'date', label: 'Date' },
  { key: 'start_time', label: 'Time' },
  { key: 'position', label: 'Position' },
  { key: 'worker', label: 'Worker' },
];

function SortHeader({ column, label, filters, onSort }) {
  const active = filters.sort === column;
  const nextDir = active && filters.dir === 'asc' ? 'desc' : 'asc';

  return (
    <th>
      <button
        type="button"
        className="sort-header-button"
        onClick={() => onSort({ sort: column, dir: nextDir, page: '' })}
      >
        {label}
        <ArrowUpDown size={12} className={active ? 'text-foreground' : 'text-muted-foreground'} />
        {active ? <span className="sr-only">{filters.dir === 'asc' ? '(ascending)' : '(descending)'}</span> : null}
      </button>
    </th>
  );
}

export function SearchResultsTable({ results, total, filters, onSort, onSelect }) {
  return (
    <div className="card mt-3">
      <div className="flex items-center justify-between border-b border-border px-4 py-2 text-sm text-muted-foreground">
        <span>{total} result{total === 1 ? '' : 's'}</span>
      </div>
      <div className="max-h-[calc(100vh-360px)] overflow-auto">
        <table className="table table-sticky-header" aria-label="Shift search results">
          <thead>
            <tr>
              {SORTABLE_COLUMNS.map((column) => (
                <SortHeader key={column.key} column={column.key} label={column.label} filters={filters} onSort={onSort} />
              ))}
              <th>Manager</th>
              <th>Status</th>
              <th>Capacity</th>
            </tr>
          </thead>
          <tbody>
            {results.length === 0 ? (
              <tr>
                <td colSpan={7}>
                  <div className="flex flex-col items-center justify-center p-8 text-center">
                    <div className="text-lg font-medium">No shifts match your search</div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Try adjusting the filters or clearing the search.
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              results.map((shift) => (
                <tr key={shift.id} className="search-result-row" onClick={() => onSelect(shift.id)}>
                  <td className="font-medium">{formatDateDMY(shift.date)}</td>
                  <td className="text-sm">
                    {shift.start_time}-{shift.end_time}
                  </td>
                  <td>
                    <span className="badge badge-default">{shift.position}</span>
                  </td>
                  <td className="text-sm">
                    {shift.worker_names.length === 0 ? (
                      <span className="text-muted-foreground">Unassigned</span>
                    ) : (
                      shift.worker_names.join(', ')
                    )}
                  </td>
                  <td className="text-sm">{shift.manager_name}</td>
                  <td>
                    <span className={`badge ${shift.status === 'draft' ? 'badge-outline' : 'badge-success'}`}>
                      {shift.status === 'draft' ? 'Draft' : 'Published'}
                    </span>
                  </td>
                  <td className="text-sm">
                    {shift.assigned_count}/{shift.capacity}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
