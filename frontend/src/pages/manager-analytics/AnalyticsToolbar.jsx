import { DateRangeControl, MultiSelectFilter } from '../../components/FilterControls.jsx';
import { ChevronDown, Download, RefreshCw } from '../../components/Icons.jsx';
import { Dropdown } from '../../components/Menus.jsx';

function timeAgo(date) {
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.round(seconds / 60)}m ago`;
}

export function AnalyticsToolbar({
  positions,
  workers,
  managers,
  filters,
  onChange,
  csvExportUrl,
  onExportPdf,
  refreshing,
  lastUpdated,
}) {
  return (
    <div className="card page-toolbar-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold">Workforce Analytics</h1>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground" aria-live="polite">
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            Updated {timeAgo(lastUpdated)}
          </span>

          <Dropdown
            trigger={({ toggle }) => (
              <button className="btn btn-outline btn-sm" type="button" onClick={toggle}>
                <Download size={14} />
                Export
                <ChevronDown size={14} />
              </button>
            )}
          >
            {({ close }) => (
              <>
                <a className="dropdown-item" href={csvExportUrl} onClick={close}>
                  Export CSV (raw data)
                </a>
                <button
                  className="dropdown-item"
                  type="button"
                  onClick={() => {
                    close();
                    onExportPdf();
                  }}
                >
                  Export PDF (report)
                </button>
              </>
            )}
          </Dropdown>
        </div>
      </div>

      <div className="search-filters-row mt-3">
        <DateRangeControl
          from={filters.dateFrom}
          to={filters.dateTo}
          onChangeFrom={(value) => onChange({ dateFrom: value })}
          onChangeTo={(value) => onChange({ dateTo: value })}
        />

        <div className="flex items-center gap-2">
          <span className="form-label mb-0">Position:</span>
          <MultiSelectFilter
            label="Positions"
            options={positions}
            selected={filters.position}
            onApply={(selected) => onChange({ position: selected })}
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="form-label mb-0">Worker:</span>
          <MultiSelectFilter
            label="Workers"
            options={workers}
            selected={filters.worker}
            onApply={(selected) => onChange({ worker: selected })}
            emptyMessage="No workers yet."
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="form-label mb-0">Manager:</span>
          <MultiSelectFilter
            label="Managers"
            options={managers}
            selected={filters.manager}
            onApply={(selected) => onChange({ manager: selected })}
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="form-label mb-0" htmlFor="analyticsStatus">
            Status:
          </label>
          <select
            id="analyticsStatus"
            className="form-select"
            value={filters.status}
            onChange={(event) => onChange({ status: event.target.value })}
          >
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </div>
      </div>
    </div>
  );
}
