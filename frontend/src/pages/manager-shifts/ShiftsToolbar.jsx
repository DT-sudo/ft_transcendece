import { addMonths, formatMonth, navigateWith } from '../../app/dates.js';
import { CalendarNav } from '../../components/Calendar.jsx';
import { CsrfInput } from '../../components/Field.jsx';
import { Plus } from '../../components/Icons.jsx';

const STATUS_OPTIONS = [
  { id: 'draft', name: 'Draft' },
  { id: 'published', name: 'Published' },
];
const SHOW_OPTIONS = [{ id: 'understaffed', name: 'Understaffed' }];

/** A filter reloads the page with the new query parameter; the server does the filtering. */
function Filter({ id, label, param, value, options }) {
  return (
    <>
      <label className="form-label mb-0" htmlFor={id}>
        {label}
      </label>
      <select id={id} className="form-select w-auto" value={value} onChange={(event) => navigateWith({ [param]: event.target.value })}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </>
  );
}

export function ShiftsToolbar({ data, onCreateShift }) {
  const { anchor, today, positions, filters, urls } = data;

  return (
    <div className="card page-toolbar-card">
      <div className="shifts-toolbar">
        <div className="shifts-toolbar-left flex min-w-0 flex-wrap items-center gap-3 justify-self-start">
          <Filter id="positionFilter" label="Position:" param="positions" value={filters.positions[0] ?? ''} options={positions} />
          <Filter id="statusFilter" label="Status:" param="status" value={filters.status} options={STATUS_OPTIONS} />
          <Filter id="showFilter" label="Show:" param="show" value={filters.understaffed ? 'understaffed' : ''} options={SHOW_OPTIONS} />
        </div>

        <div className="shifts-toolbar-center min-w-0 justify-self-center">
          <div className="calendar-period">{formatMonth(anchor)}</div>
        </div>

        <div className="shifts-toolbar-right flex min-w-0 flex-wrap items-center justify-end gap-3 justify-self-end">
          <CalendarNav
            onPrev={() => navigateWith({ date: addMonths(anchor, -1) })}
            onNext={() => navigateWith({ date: addMonths(anchor, 1) })}
            onToday={() => navigateWith({ date: today })}
          />

          <button className="btn btn-primary" type="button" onClick={onCreateShift}>
            <Plus size={16} />
            Add
          </button>

          <form method="post" action={urls.publishAll} className="inline">
            <CsrfInput />
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
