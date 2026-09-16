import { useEffect, useRef, useState } from 'react';

import { isRtl, t } from '../../i18n/index.js';

// Plain SVG charts; the project has no chart library.

const HEIGHT = 200;
const PAD = { top: 14, right: 14, bottom: 28, left: 36 };
const PLOT_HEIGHT = HEIGHT - PAD.top - PAD.bottom;
const MAX_BAR_WIDTH = 48;
const MAX_LABEL_LENGTH = 10;

export function EmptyChart() {
  return <p className="chart-empty">{t('analytics.noData')}</p>;
}

/** The element's rendered width, so the viewBox matches its box and text never stretches. */
function useWidth() {
  const ref = useRef(null);
  const [width, setWidth] = useState(640);

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(120, Math.round(entry.contentRect.width))));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return [ref, width];
}

const truncate = (text) => (text.length > MAX_LABEL_LENGTH ? `${text.slice(0, MAX_LABEL_LENGTH - 1)}…` : text);

/**
 * Line or bar chart of `data[i][valueKey]` with a hover tooltip. Points sit in the
 * middle of equal slots, so both kinds share one x scale. Right to left, the whole
 * chart mirrors: the first point and the value axis move to the right.
 */
export function XYChart({ kind, label, data, labelKey, valueKey, formatLabel = String, formatValue = String, color = 'var(--color-primary)' }) {
  const [ref, width] = useWidth();
  const [hovered, setHovered] = useState(null);

  // Geometry is worked out left to right, then mirrored for RTL pages.
  const x = isRtl() ? (value) => width - value : (value) => value;
  const max = Math.max(1, ...data.map((item) => item[valueKey]));
  const slot = (width - PAD.left - PAD.right) / Math.max(1, data.length);
  const baseline = PAD.top + PLOT_HEIGHT;
  const points = data.map((item, index) => ({
    x: x(PAD.left + slot * (index + 0.5)),
    y: baseline - (item[valueKey] / max) * PLOT_HEIGHT,
    item,
  }));
  const hover = (index) => ({ onMouseEnter: () => setHovered(index), onMouseLeave: () => setHovered(null) });

  // Every bar is labelled; a line only at its two ends.
  const labelled = kind === 'bar' || points.length < 2 ? points : [points[0], points.at(-1)];
  const line = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
  const barWidth = Math.min(slot * 0.65, MAX_BAR_WIDTH);
  const tip = points[hovered];

  return (
    <div className="chart-wrap" ref={ref}>
      {data.length === 0 ? (
        <EmptyChart />
      ) : (
        <svg viewBox={`0 0 ${width} ${HEIGHT}`} className="chart-svg" role="img" aria-label={label}>
          {[0, 0.5, 1].map((fraction) => (
            <line key={fraction} className="chart-gridline" x1={x(PAD.left)} x2={x(width - PAD.right)} y1={PAD.top + PLOT_HEIGHT * fraction} y2={PAD.top + PLOT_HEIGHT * fraction} />
          ))}
          {/* text-anchor "end" follows the page direction, so these labels hug the plot on both sides. */}
          <text className="chart-axis-label" x={x(PAD.left - 6)} y={PAD.top + 4} textAnchor="end">
            {formatValue(max)}
          </text>
          <text className="chart-axis-label" x={x(PAD.left - 6)} y={baseline} textAnchor="end">
            0
          </text>

          {kind === 'line' ? (
            <>
              <path d={`${line} L ${points.at(-1).x} ${baseline} L ${points[0].x} ${baseline} Z`} fill={color} fillOpacity={0.08} />
              <path d={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" />
              {points.map((point, index) => (
                <circle key={index} cx={point.x} cy={point.y} r={hovered === index ? 5 : 3} fill={color} {...hover(index)} />
              ))}
            </>
          ) : (
            points.map((point, index) => (
              <rect
                key={index}
                x={point.x - barWidth / 2}
                y={point.y}
                width={barWidth}
                height={baseline - point.y}
                rx={3}
                fill={color}
                opacity={hovered === null || hovered === index ? 1 : 0.55}
                {...hover(index)}
              />
            ))
          )}

          {labelled.map((point) => {
            const text = formatLabel(point.item[labelKey]);
            return (
              <text key={point.x} className="chart-axis-label" x={point.x} y={HEIGHT - 8} textAnchor="middle">
                {kind === 'bar' ? truncate(text) : text}
              </text>
            );
          })}
        </svg>
      )}

      {tip ? (
        <div className="chart-tooltip" style={{ left: `${(tip.x / width) * 100}%`, top: `${(tip.y / HEIGHT) * 100}%` }}>
          <div className="font-medium">{formatLabel(tip.item[labelKey])}</div>
          <div>{formatValue(tip.item[valueKey])}</div>
        </div>
      ) : null}
    </div>
  );
}

/**
 * One bar per worker against the legal maximum for the filtered period (`maxHours`): a gray bar
 * the height of the maximum sits behind a coloured bar the height of the hours actually worked.
 * Within the limit the bar is green and the gray shows through above it as remaining capacity;
 * over the limit the bar is red and rises past the gray, covering it.
 */
export function WorkerHoursChart({ label, data, maxHours, formatValue = String }) {
  const [ref, width] = useWidth();
  const [hovered, setHovered] = useState(null);

  const x = isRtl() ? (value) => width - value : (value) => value;
  const max = Math.max(1, maxHours, ...data.map((item) => item.hours));
  const slot = (width - PAD.left - PAD.right) / Math.max(1, data.length);
  const baseline = PAD.top + PLOT_HEIGHT;
  const barWidth = Math.min(slot * 0.65, MAX_BAR_WIDTH);
  const scale = (hours) => (hours / max) * PLOT_HEIGHT;
  const hover = (index) => ({ onMouseEnter: () => setHovered(index), onMouseLeave: () => setHovered(null) });

  const bars = data.map((item, index) => {
    const centerX = x(PAD.left + slot * (index + 0.5));
    const overtime = item.hours > maxHours;
    return { item, index, centerX, overtime, maxHeight: scale(maxHours), hoursHeight: scale(item.hours) };
  });
  const tip = bars[hovered];

  return (
    <>
      <div className="chart-wrap" ref={ref}>
        {data.length === 0 ? (
          <EmptyChart />
        ) : (
          <svg viewBox={`0 0 ${width} ${HEIGHT}`} className="chart-svg" role="img" aria-label={label}>
            {[0, 0.5, 1].map((fraction) => (
              <line key={fraction} className="chart-gridline" x1={x(PAD.left)} x2={x(width - PAD.right)} y1={PAD.top + PLOT_HEIGHT * fraction} y2={PAD.top + PLOT_HEIGHT * fraction} />
            ))}
            <text className="chart-axis-label" x={x(PAD.left - 6)} y={PAD.top + 4} textAnchor="end">
              {formatValue(max)}
            </text>
            <text className="chart-axis-label" x={x(PAD.left - 6)} y={baseline} textAnchor="end">
              0
            </text>

            {bars.map(({ index, centerX, overtime, maxHeight, hoursHeight }) => (
              <g key={index} opacity={hovered === null || hovered === index ? 1 : 0.55} {...hover(index)}>
                <rect x={centerX - barWidth / 2} y={baseline - maxHeight} width={barWidth} height={maxHeight} rx={3} fill="var(--color-shift-past)" />
                <rect
                  x={centerX - barWidth / 2}
                  y={baseline - hoursHeight}
                  width={barWidth}
                  height={hoursHeight}
                  rx={3}
                  fill={overtime ? 'var(--color-destructive)' : 'var(--color-shift-published)'}
                />
              </g>
            ))}

            {bars.map(({ item, centerX }) => (
              <text key={centerX} className="chart-axis-label" x={centerX} y={HEIGHT - 8} textAnchor="middle">
                {truncate(item.worker)}
              </text>
            ))}
          </svg>
        )}

        {tip ? (
          <div className="chart-tooltip" style={{ left: `${(tip.centerX / width) * 100}%`, top: `${((baseline - Math.max(tip.maxHeight, tip.hoursHeight)) / HEIGHT) * 100}%` }}>
            <div className="font-medium">{tip.item.worker}</div>
            <div>
              {formatValue(tip.item.hours)} / {formatValue(maxHours)}
              {tip.overtime ? ` · ${t('analytics.overtime')}` : ''}
            </div>
          </div>
        ) : null}
      </div>

      {data.length > 0 ? (
        <ul className="chart-legend chart-legend-row">
          <li className="chart-legend-item">
            <span className="chart-legend-swatch" style={{ backgroundColor: 'var(--color-shift-past)' }} aria-hidden="true" />
            {t('analytics.legalMax')}
          </li>
          <li className="chart-legend-item">
            <span className="chart-legend-swatch" style={{ backgroundColor: 'var(--color-shift-published)' }} aria-hidden="true" />
            {t('analytics.withinLimit')}
          </li>
          <li className="chart-legend-item">
            <span className="chart-legend-swatch" style={{ backgroundColor: 'var(--color-destructive)' }} aria-hidden="true" />
            {t('analytics.overtime')}
          </li>
        </ul>
      ) : null}
    </>
  );
}
