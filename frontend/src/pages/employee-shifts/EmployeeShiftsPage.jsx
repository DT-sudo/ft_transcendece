import { useMemo, useState } from 'react';

import { addMonths, formatDate, formatDuration, navigateWith, shiftDurationMinutes } from '../../app/dates.js';
import { getBootstrap, postForm } from '../../app/http.js';
import { groupShiftsByDate } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { CalendarNav, MonthCalendar } from '../../components/Calendar.jsx';
import { Modal } from '../../components/Modal.jsx';
import { useToast } from '../../components/Toasts.jsx';

function ShiftDetailsModal({ shift, onClose }) {
  return (
    <Modal
      title="Shift details"
      onClose={onClose}
      maxWidth="420px"
      footer={
        <button className="btn btn-primary" type="button" onClick={onClose}>
          Close
        </button>
      }
    >
      <div className="modal-body">
        <div className="font-medium">{formatDate(shift.date)}</div>
        <div className="mt-1 text-sm text-muted-foreground">
          {shift.start_time}-{shift.end_time}
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="badge badge-default">{shift.position}</span>
          <span className="text-sm text-muted-foreground">
            {formatDuration(shiftDurationMinutes(shift))}
          </span>
        </div>
      </div>
    </Modal>
  );
}

export function EmployeeShiftsPage() {
  return (
    <AppShell>
      <EmployeeShiftsContent />
    </AppShell>
  );
}

function EmployeeShiftsContent() {
  const { data } = getBootstrap();
  const showToast = useToast();

  const [unavailable, setUnavailable] = useState(() => new Set(data.unavailable || []));
  const [detailsShiftId, setDetailsShiftId] = useState(null);

  const shiftsByDate = useMemo(() => groupShiftsByDate(data.shifts), [data.shifts]);

  const toggleUnavailability = async (iso) => {
    try {
      const payload = await postForm(data.urls.toggleUnavailability, { date: iso });
      setUnavailable((current) => {
        const next = new Set(current);
        if (payload.unavailable) next.add(iso);
        else next.delete(iso);
        return next;
      });
    } catch (error) {
      showToast('error', 'Cannot mark unavailable', error.message || 'Could not update unavailability.');
    }
  };

  const sortedUnavailable = useMemo(() => [...unavailable].sort(), [unavailable]);
  const detailsShift = data.shifts.find((shift) => shift.id === detailsShiftId) || null;

  return (
    <>
      <main className="p-4 pt-0">
        <div className="card page-toolbar-card">
          <div className="shifts-toolbar">
            <div className="shifts-toolbar-left" />
            <div className="shifts-toolbar-center justify-self-center">
              <div className="calendar-period">{data.periodLabel}</div>
            </div>
            <div className="shifts-toolbar-right flex items-center justify-end justify-self-end">
              <CalendarNav
                onPrev={() => navigateWith({ date: addMonths(data.anchor, -1) })}
                onNext={() => navigateWith({ date: addMonths(data.anchor, 1) })}
                onToday={() => navigateWith({ date: data.today })}
              />
            </div>
          </div>
        </div>

        <div className="card mt-3">
          <MonthCalendar
            anchorISO={data.anchor}
            todayISO={data.today}
            ariaLabel="Month calendar"
            dayClassName={(day) =>
              !shiftsByDate.has(day.iso) && unavailable.has(day.iso) ? 'calendar-cell-unavailable' : ''
            }
            onDayClick={(day) => {
              if (!day.inMonth) {
                navigateWith({ date: day.iso });
                return;
              }
              // Only future days without a shift can be toggled.
              if (day.iso <= data.today || shiftsByDate.has(day.iso)) return;
              toggleUnavailability(day.iso);
            }}
            renderDay={(day) =>
              (shiftsByDate.get(day.iso) || []).map((shift) => (
                <button
                  key={shift.id}
                  type="button"
                  className={`shift-chip mb-1 ${shift.is_past ? 'shift-chip-past' : 'shift-chip-future'}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    setDetailsShiftId(shift.id);
                  }}
                >
                  {shift.start_time}-{shift.end_time}
                </button>
              ))
            }
          />
        </div>

        <div className="card mt-3">
          <div className="border-b border-border px-4 py-2.5">
            <h3 className="card-title">Unavailable days</h3>
          </div>
          <div className="p-6">
            <div className="flex flex-wrap gap-1.5" aria-label="Unavailable days list">
              {sortedUnavailable.length === 0 ? (
                <div className="text-sm text-muted-foreground">No unavailable days selected.</div>
              ) : (
                sortedUnavailable.map((iso) => {
                  const pretty = formatDate(iso);
                  return (
                    <span className="tag-chip" key={iso}>
                      <button
                        type="button"
                        className="chip-remove"
                        aria-label={`Remove ${pretty}`}
                        onClick={() => toggleUnavailability(iso)}
                      >
                        x
                      </button>
                      <span className="whitespace-nowrap">{pretty}</span>
                    </span>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </main>

      {detailsShift ? (
        <ShiftDetailsModal shift={detailsShift} onClose={() => setDetailsShiftId(null)} />
      ) : null}
    </>
  );
}
