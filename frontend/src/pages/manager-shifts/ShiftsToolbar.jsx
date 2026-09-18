import { formatDate, formatMonth, navigateWith } from '../../app/dates.js';
import { statusOptions } from '../../app/shifts.js';
import { CalendarNav, CalendarToolbar } from '../../components/Calendar.jsx';
import { FilterSelect, PostForm } from '../../components/Field.jsx';
import { Plus } from '../../components/Icons.jsx';
import { t } from '../../i18n/index.js';

/** A filter reloads the page with the new query parameter; the server does the filtering. */
const filterBy = (param) => (event) => navigateWith({ [param]: event.target.value });

export function ShiftsToolbar({ data, onCreateShift }) {
  const { view, anchor, start, end, today, positions, filters, urls } = data;
  const views = [
    { id: 'week', name: t('shifts.week') },
    { id: 'month', name: t('shifts.month') },
  ];

  return (
    <CalendarToolbar
      period={view === 'week' ? `${formatDate(start, { year: false })} – ${formatDate(end)}` : formatMonth(anchor)}
      start={
        <>
          <FilterSelect id="positionFilter" label={t('filters.position')} options={positions} value={filters.position} onChange={filterBy('position')} />
          <FilterSelect id="statusFilter" label={t('filters.status')} options={statusOptions()} value={filters.status} onChange={filterBy('status')} />
          <FilterSelect
            id="showFilter"
            label={t('filters.show')}
            options={[{ id: 'understaffed', name: t('filters.understaffed') }]}
            value={filters.understaffed ? 'understaffed' : ''}
            onChange={filterBy('show')}
          />
        </>
      }
      end={
        <>
          <div className="flex gap-1" role="group" aria-label={t('shifts.calendarView')}>
            {views.map((option) => (
              <button
                key={option.id}
                className={`btn btn-sm ${view === option.id ? 'btn-primary' : 'btn-outline'}`}
                type="button"
                aria-pressed={view === option.id}
                onClick={() => navigateWith({ view: option.id, date: anchor })}
              >
                {option.name}
              </button>
            ))}
          </div>

          <CalendarNav anchorISO={anchor} todayISO={today} view={view} />

          <button className="btn btn-primary" type="button" onClick={onCreateShift}>
            <Plus size={16} />
            {t('shifts.add')}
          </button>

          <PostForm action={urls.publishAll} className="flex" fields={{ view, date: anchor }}>
            <button className="btn btn-outline" type="submit">
              {t('shifts.publishAll')}
            </button>
          </PostForm>
        </>
      }
    />
  );
}
