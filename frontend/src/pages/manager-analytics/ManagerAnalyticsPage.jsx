import { useState } from 'react';

import { formatDate } from '../../app/dates.js';
import { getBootstrap, getJSON } from '../../app/http.js';
import { useLiveEvents } from '../../app/live.js';
import { STATUS_OPTIONS } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { DateRangeFields, ShiftFilterSelects } from '../../components/Field.jsx';
import { ChevronDown } from '../../components/Icons.jsx';
import { Dropdown } from '../../components/Menus.jsx';
import { DonutChart, EmptyChart, XYChart } from './Charts.jsx';

const KPIS = [
  { key: 'shifts', label: 'Shifts', accent: 'var(--color-primary)' },
  { key: 'workers', label: 'Workers', accent: 'var(--color-info)' },
  { key: 'hours', label: 'Hours', accent: 'var(--color-shift-published)', suffix: 'h' },
  { key: 'open_shifts', label: 'Open shifts', accent: 'var(--color-warning)' },
];

const STATUS_COLORS = { draft: 'var(--color-shift-past)', published: 'var(--color-shift-published)' };

const plural = (count, noun) => `${count} ${noun}${count === 1 ? '' : 's'}`;

/** Name of the selected `{ id, name }` option, or "All" when the filter is empty. */
const nameOf = (options, id) => options.find((option) => String(option.id) === id)?.name ?? 'All';

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
  const { data } = getBootstrap();
  const { positions, workers, filters, urls } = data;
  const [analytics, setAnalytics] = useState(data.analytics);

  // Every shift write pushes `shifts.changed`: re-fetch the numbers for the same filters.
  // A failed refresh leaves the last numbers on screen.
  const refresh = () => getJSON(`${urls.data}${window.location.search}`).then(setAnalytics).catch(() => {});
  useLiveEvents(
    (event) => {
      if (event.type === 'shifts.changed') refresh();
    },
    { onReconnect: refresh },
  );

  const topPositions = [...analytics.by_position].sort((a, b) => b.count - a.count).slice(0, 5);

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <form className="card page-toolbar-card filter-bar no-print" method="get">
          <DateRangeFields from={filters.date_from} to={filters.date_to} />
          <ShiftFilterSelects filters={filters} positions={positions} workers={workers} />
          <button className="btn btn-primary" type="submit">
            Apply
          </button>

          <div className="ms-auto">
            <Dropdown
              trigger={({ toggle }) => (
                <button className="btn btn-outline" type="button" onClick={toggle} aria-haspopup="menu">
                  Export
                  <ChevronDown />
                </button>
              )}
            >
              {/* The CSV is an attachment, so the page stays; the browser's print dialog saves the PDF. */}
              <button className="dropdown-item" type="button" onClick={() => window.location.assign(`${urls.exportCsv}${window.location.search}`)}>
                CSV (raw data)
              </button>
              <button className="dropdown-item" type="button" onClick={() => window.print()}>
                PDF (report)
              </button>
            </Dropdown>
          </div>
        </form>

        <div className="print-only mb-4">
          <h1 className="text-xl font-semibold">Workforce Analytics Report</h1>
          <p className="text-sm text-muted-foreground">
            {formatDate(filters.date_from)} – {formatDate(filters.date_to)} · Position: {nameOf(positions, filters.position)} · Worker:{' '}
            {nameOf(workers, filters.worker)} · Status: {nameOf(STATUS_OPTIONS, filters.status)}
          </p>
          <p className="text-xs text-muted-foreground">Generated {new Date().toLocaleString()}</p>
        </div>

        <div className="kpi-grid mt-3">
          {KPIS.map((kpi) => (
            <div key={kpi.key} className="kpi-card" style={{ '--kpi-accent': kpi.accent }}>
              <div className="kpi-card-label">{kpi.label}</div>
              <div className="kpi-card-value">
                {analytics.kpis[kpi.key]}
                {kpi.suffix}
              </div>
            </div>
          ))}
        </div>

        <div className="analytics-grid mt-3">
          <ChartCard title="Shifts over time" wide>
            <XYChart
              kind="line"
              label="Shifts over time"
              data={analytics.by_date}
              labelKey="date"
              valueKey="count"
              formatLabel={(iso) => formatDate(iso, { year: false })}
            />
          </ChartCard>

          <ChartCard title="Shifts by position">
            <XYChart kind="bar" label="Shifts by position" data={analytics.by_position} labelKey="position" valueKey="count" />
          </ChartCard>

          <ChartCard title="Shift status">
            <DonutChart
              label="Shift status"
              segments={analytics.by_status.map(({ status, count }) => ({
                label: nameOf(STATUS_OPTIONS, status),
                value: count,
                color: STATUS_COLORS[status],
              }))}
            />
          </ChartCard>

          <ChartCard title="Hours per worker" wide>
            <XYChart
              kind="bar"
              label="Hours per worker"
              data={analytics.top_workers}
              labelKey="worker"
              valueKey="hours"
              formatValue={(hours) => `${hours}h`}
              color="var(--color-shift-published)"
            />
          </ChartCard>

          <ChartCard title="Top workers">
            <TopList items={analytics.top_workers.slice(0, 5)} name="worker" detail={(w) => `${w.hours}h · ${plural(w.shifts, 'shift')}`} />
          </ChartCard>

          <ChartCard title="Top positions">
            <TopList items={topPositions} name="position" detail={(p) => plural(p.count, 'shift')} />
          </ChartCard>
        </div>
      </main>
    </AppShell>
  );
}
