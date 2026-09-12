import { useState } from 'react';

import { SelectPopover } from './Menus.jsx';

function summarizeLabel(allLabel, options, selected) {
  if (selected.length === 0 || selected.length === options.length) return allLabel;
  const names = options.filter((option) => selected.includes(String(option.id))).map((o) => o.name);
  return names.length <= 2 ? names.join(', ') : `${names.length} selected`;
}

/**
 * Generic "All ▾" multiselect popover used by every filter in the Search and
 * Analytics toolbars (position/worker/manager, etc). Mirrors the calendar
 * toolbar's PositionFilter, generalised over an arbitrary option list so the
 * two new pages don't duplicate five near-identical filters each.
 */
export function MultiSelectFilter({ label, options, selected, onApply, ariaLabel, emptyMessage }) {
  const [draft, setDraft] = useState(selected);

  const toggle = (id, checked) =>
    setDraft((current) =>
      checked ? [...current, String(id)] : current.filter((value) => value !== String(id)),
    );

  return (
    <SelectPopover
      ariaLabel={ariaLabel || `Select ${label.toLowerCase()}`}
      label={<span>{summarizeLabel(`All ${label.toLowerCase()}`, options, selected)}</span>}
    >
      {({ close }) => (
        <>
          {options.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              {emptyMessage || `No ${label.toLowerCase()} yet.`}
            </div>
          ) : (
            <div className="multiselect-menu-scroll">
              {options.map((option) => (
                <label className="multiselect-item" key={option.id}>
                  <input
                    type="checkbox"
                    checked={draft.includes(String(option.id))}
                    onChange={(event) => toggle(option.id, event.target.checked)}
                  />
                  {option.name}
                </label>
              ))}
            </div>
          )}

          <div className="multiselect-actions justify-end">
            <button className="btn btn-ghost btn-sm" type="button" onClick={() => setDraft([])}>
              Clear
            </button>
            <button
              className="btn btn-ghost btn-sm"
              type="button"
              onClick={() => setDraft(options.map((option) => String(option.id)))}
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

/** Paired "from"/"to" date inputs, styled like the rest of the form controls. */
export function DateRangeControl({ from, to, onChangeFrom, onChangeTo }) {
  return (
    <div className="flex items-center gap-2">
      <label className="form-label mb-0" htmlFor="dateFrom">
        Date:
      </label>
      <input
        id="dateFrom"
        type="date"
        className="form-input w-auto"
        value={from}
        max={to || undefined}
        onChange={(event) => onChangeFrom(event.target.value)}
      />
      <span className="text-sm text-muted-foreground">→</span>
      <input
        id="dateTo"
        type="date"
        className="form-input w-auto"
        value={to}
        min={from || undefined}
        onChange={(event) => onChangeTo(event.target.value)}
      />
    </div>
  );
}
