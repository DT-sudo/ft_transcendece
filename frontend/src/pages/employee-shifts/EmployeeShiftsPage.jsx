import { useMemo, useState } from 'react';

import { formatDate, formatMonth, navigateWith } from '../../app/dates.js';
import { getBootstrap, postForm } from '../../app/http.js';
import { useLivePageData } from '../../app/live.js';
import { groupShiftsByDate } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { CalendarNav, MonthCalendar } from '../../components/Calendar.jsx';
import { useToast } from '../../components/Notifications.jsx';

export function EmployeeShiftsPage() {
  return (
    <AppShell>
      <EmployeeShiftsContent />
    </AppShell>
  );
}

/** Published shifts for the month, updated live; clicking a free future day toggles it as unavailable. */
function EmployeeShiftsContent() {
  const data = useLivePageData(getBootstrap().data);
  const showToast = useToast();
  const [unavailable, setUnavailable] = useState(() => new Set(data.unavailable));
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
      showToast('success', payload.unavailable ? 'Marked unavailable' : 'Marked available', formatDate(iso));
    } catch (error) {
      showToast('error', 'Cannot mark unavailable', error.message);
    }
  };

  return (
    <main className="p-4 pt-0">
      <div className="card page-toolbar-card">
        <div className="shifts-toolbar">
          <div className="shifts-toolbar-left text-sm text-muted-foreground">Click a free future day to mark it unavailable.</div>
          <div className="shifts-toolbar-center justify-self-center">
            <div className="calendar-period">{formatMonth(data.anchor)}</div>
          </div>
          <div className="shifts-toolbar-right flex items-center justify-end justify-self-end">
            <CalendarNav anchorISO={data.anchor} todayISO={data.today} />
          </div>
        </div>
      </div>

      <div className="card calendar-fill calendar-fit mt-3">
        <MonthCalendar
          anchorISO={data.anchor}
          todayISO={data.today}
          ariaLabel="Month calendar"
          dayClassName={(day) => (!shiftsByDate.has(day.iso) && unavailable.has(day.iso) ? 'calendar-cell-unavailable' : '')}
          onDayClick={(day) => {
            if (!day.inMonth) navigateWith({ date: day.iso });
            // Only future days without a shift can be toggled.
            else if (day.iso > data.today && !shiftsByDate.has(day.iso)) toggleUnavailability(day.iso);
          }}
          renderDay={(day) =>
            (shiftsByDate.get(day.iso) || []).map((shift) => (
              <div key={shift.id} className={`shift-chip mb-1 ${shift.is_past ? 'shift-chip-past' : 'shift-chip-future'}`}>
                {shift.start_time}-{shift.end_time} · {shift.position}
              </div>
            ))
          }
        />
      </div>
    </main>
  );
}
