import { useState } from 'react';

import { navigateWith } from '../../app/dates.js';
import { DateRangeControl, MultiSelectFilter } from '../../components/FilterControls.jsx';
import { Search } from '../../components/Icons.jsx';
import { Pagination } from '../../components/Pagination.jsx';

export function SearchToolbar({ positions, workers, managers, filters, pagination }) {
  const [queryDraft, setQueryDraft] = useState(filters.q);

  const submitQuery = (event) => {
    event.preventDefault();
    navigateWith({ q: queryDraft, page: '' });
  };

  const resetAll = () => {
    setQueryDraft('');
    window.location.assign(window.location.pathname);
  };

  return (
    <div className="card page-toolbar-card">
      <div className="flex flex-col gap-3">
        <div className="search-toolbar-top">
          <form className="flex min-w-0 flex-1 items-center gap-2" onSubmit={submitQuery}>
            <div className="relative min-w-0 flex-1">
              <Search
                size={16}
                className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground"
              />
              <input
                type="search"
                className="form-input w-full pl-9"
                placeholder="Search by worker, manager, or position…"
                value={queryDraft}
                onChange={(event) => setQueryDraft(event.target.value)}
              />
            </div>
            <button className="btn btn-primary" type="submit">
              Search
            </button>
          </form>

          {/* Pagination lives here (not below the results list) so its
              position never jumps as the number of visible rows changes
              between pages. */}
          <Pagination compact {...pagination} />
        </div>

        <div className="search-filters-row">
          <div className="flex items-center gap-2">
            <span className="form-label mb-0">Position:</span>
            <MultiSelectFilter
              label="Positions"
              options={positions}
              selected={filters.position}
              onApply={(selected) => navigateWith({ position: selected, page: '' })}
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="form-label mb-0">Worker:</span>
            <MultiSelectFilter
              label="Workers"
              options={workers}
              selected={filters.worker}
              onApply={(selected) => navigateWith({ worker: selected, page: '' })}
              emptyMessage="No workers yet."
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="form-label mb-0">Manager:</span>
            <MultiSelectFilter
              label="Managers"
              options={managers}
              selected={filters.manager}
              onApply={(selected) => navigateWith({ manager: selected, page: '' })}
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="form-label mb-0" htmlFor="statusFilter">
              Status:
            </label>
            <select
              id="statusFilter"
              className="form-select"
              value={filters.status}
              onChange={(event) => navigateWith({ status: event.target.value, page: '' })}
            >
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>

          <DateRangeControl
            from={filters.dateFrom}
            to={filters.dateTo}
            onChangeFrom={(value) => navigateWith({ date_from: value, page: '' })}
            onChangeTo={(value) => navigateWith({ date_to: value, page: '' })}
          />

          <button className="btn btn-ghost btn-sm" type="button" onClick={resetAll}>
            Clear filters
          </button>
        </div>
      </div>
    </div>
  );
}
