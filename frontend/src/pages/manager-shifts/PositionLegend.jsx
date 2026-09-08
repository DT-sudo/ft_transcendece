import { useMemo } from 'react';

import { positionPalette } from '../../app/positions.js';

/** Fixed bottom bar listing only the position colours present in the period. */
export function PositionLegend({ positions, shifts }) {
  const { visiblePositions, hasDraft } = useMemo(() => {
    const publishedPositionIds = new Set(
      shifts
        .filter((shift) => String(shift.status || '').toLowerCase() !== 'draft')
        .map((shift) => String(shift.position_id ?? ''))
        .filter(Boolean),
    );

    return {
      hasDraft: shifts.some((shift) => String(shift.status || '').toLowerCase() === 'draft'),
      visiblePositions: positions
        .filter((position) => publishedPositionIds.has(String(position.id)))
        .sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''))),
    };
  }, [positions, shifts]);

  return (
    <div className="legend-bar">
      <div
        className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 overflow-hidden"
        aria-label="Position color legend"
      >
        {hasDraft ? (
          <div className="inline-flex items-center gap-2 text-sm">
            <span className="position-swatch position-swatch-draft" aria-hidden="true" />
            <span>Draft</span>
          </div>
        ) : null}

        {visiblePositions.map((position) => (
          <div className="inline-flex items-center gap-2 text-sm" key={position.id}>
            <span className="position-swatch" style={positionPalette(position.id)} aria-hidden="true" />
            <span>{position.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
