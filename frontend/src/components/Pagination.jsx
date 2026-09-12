import { ChevronLeft, ChevronRight } from './Icons.jsx';

/**
 * `compact` drops the "Showing X-Y of Z" text and tightens spacing, for use
 * inside a filter toolbar rather than below a results list — a fixed spot
 * that doesn't move around as the number of visible rows changes.
 */
export function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  pageSizeChoices,
  onPageChange,
  onPageSizeChange,
  compact = false,
}) {
  const firstRow = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRow = Math.min(total, page * pageSize);

  return (
    <div className={compact ? 'search-pagination' : 'flex flex-wrap items-center justify-between gap-3 px-1 py-2'}>
      {!compact ? (
        <div className="text-sm text-muted-foreground">
          {total === 0 ? 'No results' : `Showing ${firstRow}–${lastRow} of ${total}`}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        {pageSizeChoices ? (
          <div className="flex items-center gap-2">
            <label className="form-label mb-0" htmlFor="pageSize">
              Per page:
            </label>
            <select
              id="pageSize"
              className="form-select"
              value={pageSize}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
            >
              {pageSizeChoices.map((choice) => (
                <option key={choice} value={choice}>
                  {choice}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <div className="flex items-center gap-2">
          <button
            className="btn btn-outline btn-icon"
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Previous page"
          >
            <ChevronLeft />
          </button>
          <span className="text-sm whitespace-nowrap">
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-outline btn-icon"
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            aria-label="Next page"
          >
            <ChevronRight />
          </button>
        </div>
      </div>
    </div>
  );
}
