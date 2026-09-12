const SECTIONS = [
  {
    key: 'workers',
    title: 'Top Workers',
    primary: 'worker',
    render: (item) => `${item.hours}h · ${item.shifts} shift${item.shifts === 1 ? '' : 's'}`,
  },
  {
    key: 'managers',
    title: 'Top Managers',
    primary: 'manager',
    render: (item) => `${item.shifts} shift${item.shifts === 1 ? '' : 's'}`,
  },
  {
    key: 'positions',
    title: 'Top Positions',
    primary: 'position',
    render: (item) => `${item.shifts} shift${item.shifts === 1 ? '' : 's'}`,
  },
];

export function TopListsPanel({ top }) {
  return (
    <div className="card">
      <div className="chart-card-title">Top Workers / Managers / Positions</div>
      <div className="top-lists-grid">
        {SECTIONS.map((section) => {
          const items = top?.[section.key] || [];
          return (
            <div key={section.key}>
              <div className="mb-2 text-sm font-medium text-muted-foreground">{section.title}</div>
              {items.length === 0 ? (
                <div className="text-sm text-muted-foreground">No data yet.</div>
              ) : (
                <ol className="flex flex-col gap-1.5">
                  {items.map((item, index) => (
                    <li key={item[section.primary]} className="flex items-center justify-between gap-2 text-sm">
                      <span className="truncate">
                        <span className="mr-1.5 text-muted-foreground">{index + 1}.</span>
                        {item[section.primary]}
                      </span>
                      <span className="badge badge-default shrink-0">{section.render(item)}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
