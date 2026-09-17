import { useEffect, useRef, useState } from 'react';

import { isRtl, t } from '../../i18n/index.js';

// Plain SVG charts; the project has no chart library.

const HEIGHT = 200;
const PAD = { top: 14, right: 14, bottom: 28, left: 36 };
const PLOT_HEIGHT = HEIGHT - PAD.top - PAD.bottom;
const BASELINE = PAD.top + PLOT_HEIGHT;
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
 * The geometry both charts share: `count` equal slots with a point in the middle of each, and
 * heights scaled to `max`. Worked out left to right, then mirrored by `x` for RTL pages, so the
 * first point and the value axis move to the right.
 */
function usePlot(count, max) {
  const [ref, width] = useWidth();
  const x = isRtl() ? (value) => width - value : (value) => value;
  const slot = (width - PAD.left - PAD.right) / Math.max(1, count);

  return {
    ref,
    width,
    x,
    barWidth: Math.min(slot * 0.65, MAX_BAR_WIDTH),
    center: (index) => x(PAD.left + slot * (index + 0.5)),
    height: (value) => (value / max) * PLOT_HEIGHT,
  };
}

/** What both charts draw around their marks: two gridlines, the value axis, and the labels under it. */
function Axes({ plot, top, labels }) {
  const { x, width } = plot;

  return (
    <>
      {[0, 0.5, 1].map((fraction) => (
        <line key={fraction} className="chart-gridline" x1={x(PAD.left)} x2={x(width - PAD.right)} y1={PAD.top + PLOT_HEIGHT * fraction} y2={PAD.top + PLOT_HEIGHT * fraction} />
      ))}
      {/* text-anchor "end" follows the page direction, so these labels hug the plot on both sides. */}
      <text className="chart-axis-label" x={x(PAD.left - 6)} y={PAD.top + 4} textAnchor="end">
        {top}
      </text>
      <text className="chart-axis-label" x={x(PAD.left - 6)} y={BASELINE} textAnchor="end">
        0
      </text>
      {labels.map(({ at, text }) => (
        <text key={at} className="chart-axis-label" x={at} y={HEIGHT - 8} textAnchor="middle">
          {text}
        </text>
      ))}
    </>
  );
}

/** Line or bar chart of `data[i][valueKey]`, with a hover tooltip. */
export function XYChart({ kind, label, data, labelKey, valueKey, formatLabel = String, formatValue = String, color = 'var(--color-primary)' }) {
  const [hovered, setHovered] = useState(null);
  const max = Math.max(1, ...data.map((item) => item[valueKey]));
  const plot = usePlot(data.length, max);

  const points = data.map((item, index) => ({ x: plot.center(index), y: BASELINE - plot.height(item[valueKey]), item }));
  const hover = (index) => ({ onMouseEnter: () => setHovered(index), onMouseLeave: () => setHovered(null) });

  // Every bar is labelled; a line only at its two ends.
  const labelled = kind === 'bar' || points.length < 2 ? points : [points[0], points.at(-1)];
  const line = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
  const tip = points[hovered];

  return (
    <div className="chart-wrap" ref={plot.ref}>
      {data.length === 0 ? (
        <EmptyChart />
      ) : (
        <svg viewBox={`0 0 ${plot.width} ${HEIGHT}`} className="chart-svg" role="img" aria-label={label}>
          <Axes
            plot={plot}
            top={formatValue(max)}
            labels={labelled.map((point) => {
              const text = formatLabel(point.item[labelKey]);
              return { at: point.x, text: kind === 'bar' ? truncate(text) : text };
            })}
          />

          {kind === 'line' ? (
            <>
              <path d={`${line} L ${points.at(-1).x} ${BASELINE} L ${points[0].x} ${BASELINE} Z`} fill={color} fillOpacity={0.08} />
              <path d={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" />
              {points.map((point, index) => (
                <circle key={index} cx={point.x} cy={point.y} r={hovered === index ? 5 : 3} fill={color} {...hover(index)} />
              ))}
            </>
          ) : (
            points.map((point, index) => (
              <rect
                key={index}
                x={point.x - plot.barWidth / 2}
                y={point.y}
                width={plot.barWidth}
                height={BASELINE - point.y}
                rx={3}
                fill={color}
                opacity={hovered === null || hovered === index ? 1 : 0.55}
                {...hover(index)}
              />
            ))
          )}
        </svg>
      )}

      {tip ? (
        <div className="chart-tooltip" style={{ left: `${(tip.x / plot.width) * 100}%`, top: `${(tip.y / HEIGHT) * 100}%` }}>
          <div className="font-medium">{formatLabel(tip.item[labelKey])}</div>
          <div>{formatValue(tip.item[valueKey])}</div>
        </div>
      ) : null}
    </div>
  );
}

const LEGEND = [
  { color: 'var(--color-shift-past)', label: 'analytics.legalMax' },
  { color: 'var(--color-shift-published)', label: 'analytics.withinLimit' },
  { color: 'var(--color-destructive)', label: 'analytics.overtime' },
];

/**
 * One bar per worker against the legal maximum for the filtered period (`maxHours`): a gray bar
 * the height of the maximum sits behind a coloured bar the height of the hours actually worked.
 * Within the limit the bar is green and the gray shows through above it as remaining capacity;
 * over the limit the bar is red and rises past the gray, covering it.
 */
export function WorkerHoursChart({ label, data, maxHours, formatValue = String }) {
  const [hovered, setHovered] = useState(null);
  const max = Math.max(1, maxHours, ...data.map((item) => item.hours));
  const plot = usePlot(data.length, max);

  const hover = (index) => ({ onMouseEnter: () => setHovered(index), onMouseLeave: () => setHovered(null) });
  const bars = data.map((item, index) => ({
    item,
    index,
    center: plot.center(index),
    overtime: item.hours > maxHours,
    allowed: plot.height(maxHours),
    worked: plot.height(item.hours),
  }));
  const tip = bars[hovered];

  return (
    <>
      <div className="chart-wrap" ref={plot.ref}>
        {data.length === 0 ? (
          <EmptyChart />
        ) : (
          <svg viewBox={`0 0 ${plot.width} ${HEIGHT}`} className="chart-svg" role="img" aria-label={label}>
            <Axes plot={plot} top={formatValue(max)} labels={bars.map((bar) => ({ at: bar.center, text: truncate(bar.item.worker) }))} />

            {bars.map(({ index, center, overtime, allowed, worked }) => (
              <g key={index} opacity={hovered === null || hovered === index ? 1 : 0.55} {...hover(index)}>
                <rect x={center - plot.barWidth / 2} y={BASELINE - allowed} width={plot.barWidth} height={allowed} rx={3} fill="var(--color-shift-past)" />
                <rect
                  x={center - plot.barWidth / 2}
                  y={BASELINE - worked}
                  width={plot.barWidth}
                  height={worked}
                  rx={3}
                  fill={overtime ? 'var(--color-destructive)' : 'var(--color-shift-published)'}
                />
              </g>
            ))}
          </svg>
        )}

        {tip ? (
          <div className="chart-tooltip" style={{ left: `${(tip.center / plot.width) * 100}%`, top: `${((BASELINE - Math.max(tip.allowed, tip.worked)) / HEIGHT) * 100}%` }}>
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
          {LEGEND.map(({ color, label: key }) => (
            <li key={key} className="chart-legend-item">
              <span className="chart-legend-swatch" style={{ backgroundColor: color }} aria-hidden="true" />
              {t(key)}
            </li>
          ))}
        </ul>
      ) : null}
    </>
  );
}
