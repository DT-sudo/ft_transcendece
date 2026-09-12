import { useEffect, useRef, useState } from 'react';

import { getBootstrap } from '../../app/bootstrap.js';
import { formatDateDMY } from '../../app/dates.js';
import { getJSON, toQueryString } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { BarChart } from '../../components/charts/BarChart.jsx';
import { LineChart } from '../../components/charts/LineChart.jsx';
import { PieChart } from '../../components/charts/PieChart.jsx';
import { useVisiblePolling } from '../../components/hooks.js';
import { AnalyticsToolbar } from './AnalyticsToolbar.jsx';
import { KpiCards } from './KpiCards.jsx';
import { PrintReportHeader } from './PrintReportHeader.jsx';
import { TopListsPanel } from './TopListsPanel.jsx';

// No websocket/push layer exists in this project, so "real-time updates when
// shifts are created, edited, assigned, reassigned, or deleted" is delivered
// as a quiet background poll instead — see useVisiblePolling (paused in
// background tabs) and manager_analytics_data() on the backend.
const POLL_INTERVAL_MS = 20000;

function toApiParams(filters) {
  return {
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
    position: filters.position,
    worker: filters.worker,
    manager: filters.manager,
    status: filters.status,
  };
}

export function ManagerAnalyticsPage() {
  const { data } = getBootstrap();
  const { positions, workers, managers, urls } = data;

  const [filters, setFilters] = useState(data.filters);
  const [analytics, setAnalytics] = useState(data.analytics);
  const [lastUpdated, setLastUpdated] = useState(() => new Date());
  const [refreshing, setRefreshing] = useState(false);

  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  const isFirstRun = useRef(true);

  const fetchAnalytics = async (targetFilters) => {
    setRefreshing(true);
    try {
      const payload = await getJSON(urls.data, toApiParams(targetFilters));
      setAnalytics({ kpis: payload.kpis, charts: payload.charts, top: payload.top });
      setLastUpdated(new Date());
    } catch {
      // A failed refresh (e.g. a dropped poll) keeps showing the last good
      // data rather than blanking the dashboard.
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (isFirstRun.current) {
      // The initial render already has server-rendered data matching these
      // filters — no need to immediately re-fetch it.
      isFirstRun.current = false;
      return;
    }
    fetchAnalytics(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.dateFrom, filters.dateTo, filters.position, filters.worker, filters.manager, filters.status]);

  useVisiblePolling(() => fetchAnalytics(filtersRef.current), POLL_INTERVAL_MS);

  const updateFilters = (patch) => setFilters((current) => ({ ...current, ...patch }));

  const csvExportUrl = `${urls.exportCsv}?${toQueryString(toApiParams(filters))}`;
  const statusChartData = analytics.charts.status_distribution.filter((item) => item.count > 0);

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="no-print">
          <AnalyticsToolbar
            positions={positions}
            workers={workers}
            managers={managers}
            filters={filters}
            onChange={updateFilters}
            csvExportUrl={csvExportUrl}
            onExportPdf={() => window.print()}
            refreshing={refreshing}
            lastUpdated={lastUpdated}
          />
        </div>

        <PrintReportHeader filters={filters} options={{ positions, workers, managers }} generatedAt={lastUpdated} />

        <div className="mt-3">
          <KpiCards kpis={analytics.kpis} />
        </div>

        <div className="analytics-charts-grid mt-3">
          <div className="card chart-card">
            <div className="chart-card-title">Shifts Over Time</div>
            <LineChart data={analytics.charts.shifts_over_time} xKey="date" yKey="count" formatX={formatDateDMY} />
          </div>

          <div className="analytics-charts-row">
            <div className="card chart-card">
              <div className="chart-card-title">Shifts by Position</div>
              <BarChart data={analytics.charts.shifts_by_position} labelKey="position" valueKey="count" />
            </div>
            <div className="card chart-card">
              <div className="chart-card-title">Shift Status</div>
              <PieChart data={statusChartData} labelKey="status" valueKey="count" />
            </div>
          </div>

          <div className="card chart-card">
            <div className="chart-card-title">Hours per Worker</div>
            <BarChart
              data={analytics.charts.hours_per_worker}
              labelKey="worker"
              valueKey="hours"
              formatValue={(v) => `${v}h`}
              color="var(--color-shift-published)"
            />
          </div>
        </div>

        <div className="mt-3">
          <TopListsPanel top={analytics.top} />
        </div>
      </main>
    </AppShell>
  );
}
