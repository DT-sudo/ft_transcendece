import { addMonths, formatMonth, navigateWith } from '../../app/dates.js';
import { STATUS_OPTIONS } from '../../app/shifts.js';
import { CalendarNav } from '../../components/Calendar.jsx';
import { CsrfInput, FilterSelect } from '../../components/Field.jsx';
import { Plus } from '../../components/Icons.jsx';

const SHOW_OPTIONS = [{ id: 'understaffed', name: 'Understaffed' }];

/** A filter reloads the page with the new query parameter; the server does the filtering. */
const filterBy = (param) => (event) => navigateWith({ [param]: event.target.value });

export function ShiftsToolbar({ data, onCreateShift }) {
  const { anchor, today, positions, filters, urls } = data;

  return (
    <div className="card page-toolbar-card">
      <div className="shifts-toolbar">
        <div className="shifts-toolbar-left flex min-w-0 flex-wrap items-center gap-3 justify-self-start">
          <FilterSelect id="positionFilter" label="Position:" options={positions} value={filters.position} onChange={filterBy('position')} />
          <FilterSelect id="statusFilter" label="Status:" options={STATUS_OPTIONS} value={filters.status} onChange={filterBy('status')} />
          <FilterSelect id="showFilter" label="Show:" options={SHOW_OPTIONS} value={filters.understaffed ? 'understaffed' : ''} onChange={filterBy('show')} />
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
