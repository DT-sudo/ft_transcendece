import { useMemo, useState } from 'react';

import { useChartWidth } from './useChartWidth.js';

const HEIGHT = 200;
const PADDING = { top: 14, right: 14, bottom: 24, left: 34 };

/**
 * Minimal dependency-free line chart (no chart library is installed in this
 * project). The viewBox width tracks the container's real measured pixel
 * width (height is fixed via CSS), so the chart never stretches out of
 * proportion or grows oversized on wide screens. Hover shows a small tooltip
 * per point so it still reads as "interactive".
 */
export function LineChart({ data, xKey = 'x', yKey = 'y', formatX = (v) => v, formatY = (v) => v, color }) {
  const [containerRef, WIDTH] = useChartWidth(640);
  const [hoverIndex, setHoverIndex] = useState(null);
  const stroke = color || 'var(--color-primary)';

  const { points, maxY, plotHeight } = useMemo(() => {
    const plotWidth = WIDTH - PADDING.left - PADDING.right;
    const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;
    const values = data.map((d) => Number(d[yKey]) || 0);
    const maxY = Math.max(1, ...values);
    const stepX = data.length > 1 ? plotWidth / (data.length - 1) : 0;

    const points = data.map((d, index) => ({
      x: PADDING.left + (data.length > 1 ? index * stepX : plotWidth / 2),
      y: PADDING.top + plotHeight - (Number(d[yKey]) / maxY) * plotHeight,
      raw: d,
    }));

    return { points, maxY, plotHeight };
  }, [data, yKey, WIDTH]);

  if (!data || data.length === 0) {
    return (
      <div className="chart-wrap" ref={containerRef}>
        <div className="chart-empty">No data for the selected filters.</div>
      </div>
    );
  }

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${PADDING.top + plotHeight} L ${points[0].x} ${PADDING.top + plotHeight} Z`;
  const hovered = hoverIndex != null ? points[hoverIndex] : null;

  return (
    <div className="chart-wrap" ref={containerRef}>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="chart-svg" role="img" aria-label="Line chart">
        {[0, 0.5, 1].map((fraction) => (
          <line
            key={fraction}
            x1={PADDING.left}
            x2={WIDTH - PADDING.right}
            y1={PADDING.top + plotHeight * fraction}
            y2={PADDING.top + plotHeight * fraction}
            className="chart-gridline"
          />
        ))}

        <path d={areaPath} fill={stroke} fillOpacity={0.08} stroke="none" />
        <path d={linePath} fill="none" stroke={stroke} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

        {points.map((p, index) => (
          <circle
            key={index}
            cx={p.x}
            cy={p.y}
            r={hoverIndex === index ? 5 : 3}
            fill={stroke}
            className="chart-point"
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex((current) => (current === index ? null : current))}
          />
        ))}

        <text x={PADDING.left} y={HEIGHT - 6} className="chart-axis-label">
          {formatX(data[0][xKey])}
        </text>
        <text x={WIDTH - PADDING.right} y={HEIGHT - 6} textAnchor="end" className="chart-axis-label">
          {formatX(data[data.length - 1][xKey])}
        </text>
        <text x={PADDING.left - 6} y={PADDING.top + 4} textAnchor="end" className="chart-axis-label">
          {formatY(maxY)}
        </text>
        <text x={PADDING.left - 6} y={PADDING.top + plotHeight} textAnchor="end" className="chart-axis-label">
          0
        </text>
      </svg>

      {hovered ? (
        <div
          className="chart-tooltip"
          style={{ left: `${(hovered.x / WIDTH) * 100}%`, top: `${(hovered.y / HEIGHT) * 100}%` }}
        >
          <div className="font-medium">{formatX(hovered.raw[xKey])}</div>
          <div>{formatY(hovered.raw[yKey])}</div>
        </div>
      ) : null}
    </div>
  );
}
