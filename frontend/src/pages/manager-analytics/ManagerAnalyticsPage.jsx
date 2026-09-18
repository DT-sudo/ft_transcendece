import { formatDate, formatHours, formatNow } from '../../app/dates.js';
import { useLivePageData } from '../../app/live.js';
import { statusOptions } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { DateRangeFields, ShiftFilterSelects } from '../../components/Field.jsx';
import { ChevronDown } from '../../components/Icons.jsx';
import { Dropdown } from '../../components/Menus.jsx';
import { t } from '../../i18n/index.js';
import { EmptyChart, LineChart, WorkerHoursChart } from './Charts.jsx';

const KPIS = [
  { key: 'shifts', label: 'analytics.shifts', accent: 'var(--color-primary)' },
  { key: 'workers', label: 'analytics.workers', accent: 'var(--color-info)' },
  { key: 'hours', label: 'analytics.hours', accent: 'var(--color-shift-published)', format: formatHours },
  { key: 'open_shifts', label: 'analytics.openShifts', accent: 'var(--color-warning)' },
];

const shiftCount = (count) => t('analytics.shiftCount', { count });

/** Name of the selected `{ id, name }` option, or "All" when the filter is empty. */
const nameOf = (options, id) => options.find((option) => String(option.id) === id)?.name ?? t('common.all');

function ChartCard({ title, wide = false, children }) {
  return (
    <section className={`card chart-card ${wide ? 'chart-card-wide' : ''}`}>
      <h2 className="chart-card-title">{title}</h2>
      {children}
    </section>
  );
}

function TopList({ items, name, detail }) {
  if (!items.length) return <EmptyChart />;
  return (
    <ol className="flex flex-col gap-1.5">
      {items.map((item, index) => (
        <li key={index} className="flex items-center justify-between gap-2 text-sm">
          <span className="truncate">
            <span className="me-1.5 text-muted-foreground">{index + 1}.</span>
            {item[name]}
          </span>
          <span className="badge badge-default shrink-0">{detail(item)}</span>
        </li>
      ))}
    </ol>
  );
}

/** KPIs, charts and top lists over the manager's shifts, filtered like the search page. */
export function ManagerAnalyticsPage() {
  // Every shift write pushes `shifts.changed`: the page re-reads its data for the same filters.
  // A failed refresh leaves the last numbers on screen.
  const { positions, workers, filters, urls, analytics } = useLivePageData();

  const topPositions = [...analytics.by_position].sort((a, b) => b.count - a.count).slice(0, 5);
  const statuses = statusOptions();

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <form className="card page-toolbar-card filter-bar no-print" method="get">
          <DateRangeFields from={filters.date_from} to={filters.date_to} />
          <ShiftFilterSelects filters={filters} positions={positions} workers={workers} />
          <button className="btn btn-primary" type="submit">
            {t('common.apply')}
          </button>

          <div className="ms-auto">
            <Dropdown
              trigger={({ toggle }) => (
                <button className="btn btn-outline" type="button" onClick={toggle} aria-haspopup="menu">
                  {t('analytics.export')}
                  <ChevronDown />
                </button>
              )}
            >
              {/* The CSV is an attachment, so the page stays; the browser's print dialog saves the PDF. */}
              <button className="dropdown-item" type="button" onClick={() => window.location.assign(`${urls.exportCsv}${window.location.search}`)}>
                {t('analytics.csv')}
              </button>
              <button className="dropdown-item" type="button" onClick={() => window.print()}>
                {t('analytics.pdf')}
              </button>
            </Dropdown>
          </div>
        </form>

        <div className="print-only mb-4">
          <h1 className="text-xl font-semibold">{t('analytics.reportTitle')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('analytics.reportFilters', {
              from: formatDate(filters.date_from),
              to: formatDate(filters.date_to),
              position: nameOf(positions, filters.position),
              worker: nameOf(workers, filters.worker),
              status: nameOf(statuses, filters.status),
            })}
          </p>
          <p className="text-xs text-muted-foreground">{t('analytics.generated', { time: formatNow() })}</p>
        </div>

        <div className="kpi-grid mt-3">
          {KPIS.map((kpi) => (
            <div key={kpi.key} className="kpi-card" style={{ '--kpi-accent': kpi.accent }}>
              <div className="kpi-card-label">{t(kpi.label)}</div>
              <div className="kpi-card-value">{kpi.format ? kpi.format(analytics.kpis[kpi.key]) : analytics.kpis[kpi.key]}</div>
            </div>
          ))}
        </div>

        <div className="analytics-grid mt-3">
          <ChartCard title={t('analytics.overTime')} wide>
            <LineChart
              label={t('analytics.overTime')}
              data={analytics.by_date}
              labelKey="date"
              valueKey="count"
              formatLabel={(iso) => formatDate(iso, { year: false })}
            />
          </ChartCard>

          <ChartCard title={t('analytics.hoursPerWorker')} wide>
            <WorkerHoursChart label={t('analytics.hoursPerWorker')} data={analytics.top_workers} maxHours={analytics.max_hours} formatValue={formatHours} />
          </ChartCard>

          <ChartCard title={t('analytics.topWorkers')}>
            <TopList items={analytics.top_workers.slice(0, 5)} name="worker" detail={(w) => `${formatHours(w.hours)} · ${shiftCount(w.shifts)}`} />
          </ChartCard>

          <ChartCard title={t('analytics.topPositions')}>
            <TopList items={topPositions} name="position" detail={(p) => shiftCount(p.count)} />
          </ChartCard>
        </div>
      </main>
    </AppShell>
  );
}
