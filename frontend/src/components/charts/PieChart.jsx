import { useMemo, useState } from 'react';

const SIZE = 220;
const CENTER = SIZE / 2;
const RADIUS = 90;
const INNER_RADIUS = 52; // donut hole

const PALETTE = [
  'var(--color-primary)',
  'var(--color-shift-published)',
  'var(--color-warning)',
  'var(--color-info)',
  'hsl(280 65% 60%)',
  'hsl(340 75% 55%)',
  'var(--color-muted-foreground)',
];

function polarPoint(radius, angle) {
  return {
    x: CENTER + radius * Math.cos(angle),
    y: CENTER + radius * Math.sin(angle),
  };
}

function segmentPath(startAngle, endAngle) {
  const outerStart = polarPoint(RADIUS, startAngle);
  const outerEnd = polarPoint(RADIUS, endAngle);
  const innerStart = polarPoint(INNER_RADIUS, endAngle);
  const innerEnd = polarPoint(INNER_RADIUS, startAngle);
  const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${RADIUS} ${RADIUS} 0 ${largeArc} 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerStart.x} ${innerStart.y}`,
    `A ${INNER_RADIUS} ${INNER_RADIUS} 0 ${largeArc} 0 ${innerEnd.x} ${innerEnd.y}`,
    'Z',
  ].join(' ');
}

/** Minimal dependency-free donut chart with a colour-keyed legend. */
export function PieChart({ data, labelKey = 'label', valueKey = 'value', formatValue = (v) => v }) {
  const [hoverIndex, setHoverIndex] = useState(null);

  const { segments, total } = useMemo(() => {
    const total = data.reduce((sum, d) => sum + (Number(d[valueKey]) || 0), 0);
    let angle = -Math.PI / 2;

    const segments = data.map((d, index) => {
      const value = Number(d[valueKey]) || 0;
      const fraction = total > 0 ? value / total : 0;
      const startAngle = angle;
      const endAngle = angle + fraction * Math.PI * 2;
      angle = endAngle;
      return {
        raw: d,
        value,
        fraction,
        color: PALETTE[index % PALETTE.length],
        path: fraction > 0 ? segmentPath(startAngle, endAngle) : null,
      };
    });

    return { segments, total };
  }, [data, valueKey]);

  if (!data || data.length === 0 || total === 0) {
    return <div className="chart-empty">No data for the selected filters.</div>;
  }

  return (
    <div className="chart-pie-layout">
      <div className="chart-wrap chart-wrap-pie">
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="chart-svg" role="img" aria-label="Pie chart">
          {segments.map((segment, index) =>
            segment.path ? (
              <path
                key={index}
                d={segment.path}
                fill={segment.color}
                opacity={hoverIndex === null || hoverIndex === index ? 1 : 0.45}
                onMouseEnter={() => setHoverIndex(index)}
                onMouseLeave={() => setHoverIndex((current) => (current === index ? null : current))}
              />
            ) : null,
          )}
          <text x={CENTER} y={CENTER - 4} textAnchor="middle" className="chart-donut-total">
            {total}
          </text>
          <text x={CENTER} y={CENTER + 14} textAnchor="middle" className="chart-axis-label">
            total
          </text>
        </svg>
      </div>

      <ul className="chart-legend">
        {segments.map((segment, index) => (
          <li
            key={index}
            className={`chart-legend-item ${hoverIndex === index ? 'chart-legend-item-active' : ''}`}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex((current) => (current === index ? null : current))}
          >
            <span className="chart-legend-swatch" style={{ backgroundColor: segment.color }} aria-hidden="true" />
            <span className="capitalize">{segment.raw[labelKey]}</span>
            <span className="text-muted-foreground">
              {formatValue(segment.value)} ({Math.round(segment.fraction * 100)}%)
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
