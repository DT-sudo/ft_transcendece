import { useState } from 'react';

import { addDays, addMonths, navigateWith } from '../../app/dates.js';
import { CalendarNav } from '../../components/Calendar.jsx';
import { Plus } from '../../components/Icons.jsx';
import { SelectPopover } from '../../components/Menus.jsx';
import { CsrfInput } from '../../components/Field.jsx';

function positionLabel(positions, selected) {
  if (selected.length === 0 || selected.length === positions.length) return 'All positions';
  const names = positions.filter((position) => selected.includes(String(position.id))).map((p) => p.name);
  return names.length <= 2 ? names.join(', ') : `${names.length} positions`;
}

function PositionFilter({ positions, selected, onApply }) {
  // No filter in the URL means every position is shown, so start from all ticked.
  const [draft, setDraft] = useState(() =>
    selected.length ? selected : positions.map((position) => String(position.id)),
  );

  const toggle = (id, checked) =>
    setDraft((current) =>
      checked ? [...current, String(id)] : current.filter((value) => value !== String(id)),
    );

  return (
    <SelectPopover ariaLabel="Select positions" label={<span>{positionLabel(positions, selected)}</span>}>
      {({ close }) => (
        <>
          {positions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              No positions yet. Add positions in Team → Manage positions.
            </div>
          ) : (
            positions.map((position) => (
              <label className="multiselect-item" key={position.id}>
                <input
                  type="checkbox"
                  checked={draft.includes(String(position.id))}
                  onChange={(event) => toggle(position.id, event.target.checked)}
                />
                {position.name}
              </label>
            ))
          )}

          <div className="multiselect-actions justify-end">
            <button className="btn btn-ghost btn-sm" type="button" onClick={() => setDraft([])}>
              Clear
            </button>
            <button
              className="btn btn-ghost btn-sm"
              type="button"
              onClick={() => setDraft(positions.map((position) => String(position.id)))}
            >
              All
            </button>
            <button
              className="btn btn-primary btn-sm"
              type="button"
              onClick={() => {
                close();
                onApply(draft);
              }}
            >
              Apply
            </button>
          </div>
        </>
      )}
    </SelectPopover>
  );
}

export function ShiftsToolbar({ data, onCreateShift }) {
  const { view, anchor, today, periodLabel, positions, filters, urls } = data;

  const step = (direction) =>
    navigateWith({
      view,
      date: view === 'month' ? addMonths(anchor, direction) : addDays(anchor, direction * 7),
    });

  return (
    <div className="card page-toolbar-card">
      <div className="shifts-toolbar">
        <div className="shifts-toolbar-left flex min-w-0 flex-wrap items-center gap-3 justify-self-start">
          <div className="flex items-center gap-2">
            <span className="form-label mb-0">Position:</span>
            <PositionFilter
              positions={positions}
              selected={filters.positions.map(String)}
              onApply={(selected) => navigateWith({ positions: selected })}
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="form-label mb-0" htmlFor="statusFilter">
              Status:
            </label>
            <select
              id="statusFilter"
              className="form-select"
              value={filters.status}
              onChange={(event) => navigateWith({ status: event.target.value })}
            >
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="form-label mb-0" htmlFor="showFilter">
              Show:
            </label>
            <select
              id="showFilter"
              className="form-select"
              value={filters.understaffed ? 'understaffed' : ''}
              onChange={(event) => navigateWith({ show: event.target.value })}
            >
              <option value="">All</option>
              <option value="understaffed">Understaffed</option>
            </select>
          </div>
        </div>

        <div className="shifts-toolbar-center min-w-0 justify-self-center">
          <div className="calendar-period">{periodLabel}</div>
        </div>

        <div className="shifts-toolbar-right flex min-w-0 flex-wrap items-center justify-end gap-3 justify-self-end">
          <CalendarNav
            onPrev={() => step(-1)}
            onNext={() => step(1)}
            onToday={() => navigateWith({ view, date: today })}
          />

          <SelectPopover
            ariaLabel="View"
            className="min-w-0"
            label={<span>{view === 'week' ? 'Week' : 'Month'}</span>}
          >
            {['week', 'month'].map((option) => (
              <label className="multiselect-item capitalize" key={option}>
                <input
                  type="radio"
                  name="viewChoice"
                  value={option}
                  checked={view === option}
                  onChange={() => navigateWith({ view: option, date: anchor })}
                />
                {option}
              </label>
            ))}
          </SelectPopover>

          <button className="btn btn-primary" type="button" onClick={onCreateShift}>
            <Plus size={16} />
            Add
          </button>

          <form method="post" action={urls.publishAll} className="inline">
            <CsrfInput />
            <input type="hidden" name="view" value={view} readOnly />
            <input type="hidden" name="date" value={anchor} readOnly />
            <button className="btn btn-outline" type="submit">
              Publish All
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
