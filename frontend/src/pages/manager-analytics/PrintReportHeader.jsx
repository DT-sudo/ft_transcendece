function describeFilters(filters, options) {
  const parts = [`${filters.dateFrom} → ${filters.dateTo}`];

  const nameList = (ids, list) =>
    ids.length === 0 ? 'All' : ids.map((id) => list.find((o) => String(o.id) === String(id))?.name || id).join(', ');

  parts.push(`Position: ${nameList(filters.position, options.positions)}`);
  parts.push(`Worker: ${nameList(filters.worker, options.workers)}`);
  parts.push(`Manager: ${nameList(filters.manager, options.managers)}`);
  parts.push(`Status: ${filters.status ? filters.status : 'All'}`);

  return parts.join('  ·  ');
}

/**
 * Only visible via the `@media print` rules in analytics.css. "Export PDF"
 * triggers `window.print()` — there's no PDF library in this project, so the
 * browser's print-to-PDF is the export engine, and this header is what turns
 * the on-screen dashboard into a self-explanatory printed report.
 */
export function PrintReportHeader({ filters, options, generatedAt }) {
  return (
    <div className="print-only mb-4">
      <h1 className="text-xl font-semibold">Workforce Analytics Report</h1>
      <p className="text-sm text-muted-foreground">{describeFilters(filters, options)}</p>
      <p className="text-xs text-muted-foreground">Generated {generatedAt.toLocaleString()}</p>
    </div>
  );
}
