const CARDS = [
  { key: 'total_shifts', label: 'Total Shifts', format: (v) => v, accent: 'var(--color-primary)' },
  { key: 'workers', label: 'Workers', format: (v) => v, accent: 'var(--color-info)' },
  { key: 'total_hours', label: 'Hours', format: (v) => `${v}h`, accent: 'var(--color-shift-published)' },
  {
    key: 'open_shifts',
    label: 'Open Shifts',
    format: (v) => v,
    accent: 'var(--color-warning)',
    warnWhenPositive: true,
  },
];

export function KpiCards({ kpis }) {
  return (
    <div className="kpi-grid">
      {CARDS.map((card) => {
        const value = kpis?.[card.key] ?? 0;
        const needsAttention = card.warnWhenPositive && value > 0;
        return (
          <div className="kpi-card" style={{ '--kpi-accent': card.accent }} key={card.key}>
            <div className="kpi-card-label">{card.label}</div>
            <div className={`kpi-card-value ${needsAttention ? 'kpi-card-value-warning' : ''}`}>
              {card.format(value)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
