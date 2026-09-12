import { useState } from 'react';

import { getBootstrap } from '../../app/bootstrap.js';
import { navigateWith } from '../../app/dates.js';
import { AppShell } from '../../components/AppShell.jsx';
import { useReloadOnBackForward } from '../../components/hooks.js';
import { SearchResultModal } from './SearchResultModal.jsx';
import { SearchResultsTable } from './SearchResultsTable.jsx';
import { SearchToolbar } from './SearchToolbar.jsx';

export function ManagerShiftSearchPage() {
  const { data } = getBootstrap();
  const { results, total, page, pageSize, totalPages, pageSizeChoices, positions, workers, managers, filters, urls } =
    data;

  const [detailsId, setDetailsId] = useState(null);
  useReloadOnBackForward();

  const detailsShift = results.find((shift) => String(shift.id) === String(detailsId)) || null;

  const pagination = {
    page,
    totalPages,
    total,
    pageSize,
    pageSizeChoices,
    onPageChange: (nextPage) => navigateWith({ page: nextPage }),
    onPageSizeChange: (nextSize) => navigateWith({ page_size: nextSize, page: '' }),
  };

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <SearchToolbar
          positions={positions}
          workers={workers}
          managers={managers}
          filters={filters}
          pagination={pagination}
        />

        <SearchResultsTable
          results={results}
          total={total}
          filters={filters}
          onSort={(params) => navigateWith(params)}
          onSelect={setDetailsId}
        />
      </main>

      {detailsShift ? (
        <SearchResultModal shift={detailsShift} calendarUrl={urls.calendar} onClose={() => setDetailsId(null)} />
      ) : null}
    </AppShell>
  );
}
