import { formatDate, navigateWith } from '../../app/dates.js';
import { getBootstrap } from '../../app/http.js';
import { STATUS_OPTIONS } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { DateRangeFields, FilterSelect, submitForm } from '../../components/Field.jsx';
import { ChevronLeft, ChevronRight } from '../../components/Icons.jsx';

const COLUMNS = [
  { sort: 'date', label: 'Date' },
  { sort: 'time', label: 'Time' },
  { sort: 'position', label: 'Position' },
  { sort: 'worker', label: 'Workers' },
  { label: 'Status' },
  { label: 'Staffed' },
];

/**
 * The filter bar is one GET form: submitting reloads the page and the server filters,
 * sorts and paginates. Selects apply at once; the text and dates apply with Search.
 */
function SearchFilters({ filters, positions, workers }) {
  return (
    <form className="card page-toolbar-card filter-bar" method="get">
      <input
        type="search"
        name="q"
        className="form-input w-auto min-w-64 flex-auto"
        placeholder="Search by position or worker…"
        aria-label="Search shifts"
        defaultValue={filters.q}
      />
      <FilterSelect id="positionFilter" name="position" label="Position:" options={positions} defaultValue={filters.position} onChange={submitForm} />
      <FilterSelect id="workerFilter" name="worker" label="Worker:" options={workers} defaultValue={filters.worker} onChange={submitForm} />
      <FilterSelect id="statusFilter" name="status" label="Status:" options={STATUS_OPTIONS} defaultValue={filters.status} onChange={submitForm} />
      <DateRangeFields from={filters.date_from} to={filters.date_to} />
      <input type="hidden" name="sort" defaultValue={filters.sort} />
      <input type="hidden" name="dir" defaultValue={filters.dir} />
      <button className="btn btn-primary" type="submit">
        Search
      </button>
      <a className="btn btn-ghost" href={window.location.pathname}>
        Clear
      </a>
    </form>
  );
}

function SortHeader({ column, filters }) {
  if (!column.sort) return <th>{column.label}</th>;
  const active = filters.sort === column.sort;
  const ascending = filters.dir === 'asc';

  return (
    <th aria-sort={active ? (ascending ? 'ascending' : 'descending') : undefined}>
      <button
        className="sort-button"
        type="button"
        onClick={() => navigateWith({ sort: column.sort, dir: active && ascending ? 'desc' : 'asc', page: '' })}
      >
        {column.label}
        {active ? <span aria-hidden="true">{ascending ? '▲' : '▼'}</span> : null}
      </button>
    </th>
  );
}

function Pagination({ page, totalPages, total }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-2 text-sm text-muted-foreground">
      <span>
        {total} result{total === 1 ? '' : 's'}
      </span>
      <div className="flex items-center gap-2">
        <button
          className="btn btn-outline btn-icon"
          type="button"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => navigateWith({ page: page - 1 })}
        >
          <ChevronLeft />
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          className="btn btn-outline btn-icon"
          type="button"
          aria-label="Next page"
          disabled={page >= totalPages}
          onClick={() => navigateWith({ page: page + 1 })}
        >
          <ChevronRight />
        </button>
      </div>
    </div>
  );
}

/** Every shift of the manager as a searchable, sortable, paginated table. */
export function ManagerShiftSearchPage() {
  const { data } = getBootstrap();
  const { results, filters, urls } = data;

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <SearchFilters filters={filters} positions={data.positions} workers={data.workers} />

        <div className="card mt-3">
          <Pagination page={data.page} totalPages={data.totalPages} total={data.total} />
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  {COLUMNS.map((column) => (
                    <SortHeader key={column.label} column={column} filters={filters} />
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.length === 0 ? (
                  <tr>
                    <td colSpan={COLUMNS.length} className="py-8 text-center text-muted-foreground">
                      No shifts match these filters.
                    </td>
                  </tr>
                ) : (
                  results.map((shift) => (
                    <tr key={shift.id}>
                      <td>
                        <a className="font-medium text-primary hover:underline" href={`${urls.calendar}?date=${shift.date}`} title="Open in calendar">
                          {formatDate(shift.date)}
                        </a>
                      </td>
                      <td>
                        {shift.start_time}-{shift.end_time}
                      </td>
                      <td>
                        <span className="badge badge-default">{shift.position}</span>
                      </td>
                      <td>
                        {shift.workers.map((worker) => worker.name).join(', ') || <span className="text-muted-foreground">Unassigned</span>}
                      </td>
                      <td>
                        <span className={`badge ${shift.status === 'draft' ? 'badge-outline' : 'badge-success'}`}>
                          {shift.status === 'draft' ? 'Draft' : 'Published'}
                        </span>
                      </td>
                      <td>
                        {shift.workers.length}/{shift.capacity}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
