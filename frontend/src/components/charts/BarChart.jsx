import { useMemo, useState } from 'react';

import { useChartWidth } from './useChartWidth.js';

const HEIGHT = 200;
const PADDING = { top: 14, right: 14, bottom: 38, left: 34 };
const BAR_GAP_RATIO = 0.35;

/**
 * Minimal dependency-free vertical bar chart (see LineChart.jsx for why, and
 * for why the viewBox width tracks the container's measured pixel width).
 */
export function BarChart({ data, labelKey = 'label', valueKey = 'value', formatValue = (v) => v, color }) {
  const [containerRef, WIDTH] = useChartWidth(640);
  const [hoverIndex, setHoverIndex] = useState(null);
  const fill = color || 'var(--color-primary)';

  const { bars, maxValue, plotHeight } = useMemo(() => {
    const plotWidth = WIDTH - PADDING.left - PADDING.right;
    const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;
    const values = data.map((d) => Number(d[valueKey]) || 0);
    const maxValue = Math.max(1, ...values);
    const slot = data.length ? plotWidth / data.length : plotWidth;
    const barWidth = slot * (1 - BAR_GAP_RATIO);

    const bars = data.map((d, index) => {
      const value = Number(d[valueKey]) || 0;
      const barHeight = (value / maxValue) * plotHeight;
      return {
        x: PADDING.left + index * slot + (slot - barWidth) / 2,
        y: PADDING.top + plotHeight - barHeight,
        width: barWidth,
        height: barHeight,
        raw: d,
      };
    });

    return { bars, maxValue, plotHeight };
  }, [data, valueKey, WIDTH]);

  if (!data || data.length === 0) {
    return (
      <div className="chart-wrap" ref={containerRef}>
        <div className="chart-empty">No data for the selected filters.</div>
      </div>
    );
  }

  const hovered = hoverIndex != null ? bars[hoverIndex] : null;

  return (
    <div className="chart-wrap" ref={containerRef}>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="chart-svg" role="img" aria-label="Bar chart">
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

        {bars.map((bar, index) => (
          <rect
            key={index}
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={Math.max(0, bar.height)}
            rx={3}
            fill={fill}
            opacity={hoverIndex === null || hoverIndex === index ? 1 : 0.55}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex((current) => (current === index ? null : current))}
          />
        ))}

        {bars.map((bar, index) => (
          <text
            key={index}
            x={bar.x + bar.width / 2}
            y={HEIGHT - PADDING.bottom + 16}
            textAnchor="middle"
            className="chart-axis-label"
          >
            {String(bar.raw[labelKey]).length > 10
              ? `${String(bar.raw[labelKey]).slice(0, 9)}…`
              : bar.raw[labelKey]}
          </text>
        ))}

        <text x={PADDING.left - 6} y={PADDING.top + 4} textAnchor="end" className="chart-axis-label">
          {formatValue(maxValue)}
        </text>
        <text x={PADDING.left - 6} y={PADDING.top + plotHeight} textAnchor="end" className="chart-axis-label">
          0
        </text>
      </svg>

      {hovered ? (
        <div
          className="chart-tooltip"
          style={{
            left: `${((hovered.x + hovered.width / 2) / WIDTH) * 100}%`,
            top: `${(hovered.y / HEIGHT) * 100}%`,
          }}
        >
          <div className="font-medium">{hovered.raw[labelKey]}</div>
          <div>{formatValue(hovered.raw[valueKey])}</div>
        </div>
      ) : null}
    </div>
  );
}
