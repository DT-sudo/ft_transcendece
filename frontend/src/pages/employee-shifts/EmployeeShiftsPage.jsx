import { useMemo, useState } from 'react';

import { formatDate, formatMonth, navigateWith } from '../../app/dates.js';
import { postForm } from '../../app/http.js';
import { useLivePageData } from '../../app/live.js';
import { groupShiftsByDate, shiftTimeClass, shiftTimes, withDay } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { CalendarNav, CalendarToolbar, MonthCalendar } from '../../components/Calendar.jsx';
import { useToast } from '../../components/Notifications.jsx';
import { t } from '../../i18n/index.js';

export function EmployeeShiftsPage() {
  return (
    <AppShell>
      <EmployeeShiftsContent />
    </AppShell>
  );
}

/** Published shifts for the month, updated live; clicking a free future day toggles it as unavailable. */
function EmployeeShiftsContent() {
  const data = useLivePageData();
  const showToast = useToast();
  const [unavailable, setUnavailable] = useState(() => new Set(data.unavailable));
  const shiftsByDate = useMemo(() => groupShiftsByDate(data.shifts), [data.shifts]);

  const toggleUnavailability = async (iso) => {
    try {
      const payload = await postForm(data.urls.toggleUnavailability, { date: iso });
      setUnavailable((current) => withDay(current, iso, payload.unavailable));
      showToast('success', payload.unavailable ? t('employeeShifts.markedUnavailable') : t('employeeShifts.markedAvailable'), formatDate(iso));
    } catch (error) {
      showToast('error', t('employeeShifts.cannotMark'), error.message || t('common.requestFailed'));
    }
  };

  return (
    <main className="p-4 pt-0">
      <CalendarToolbar period={formatMonth(data.anchor)} end={<CalendarNav anchorISO={data.anchor} todayISO={data.today} />} />

      <div className="card calendar-fill calendar-fit mt-3">
        <MonthCalendar
          anchorISO={data.anchor}
          todayISO={data.today}
          ariaLabel={t('employeeShifts.calendar')}
          dayClassName={(day) => (!shiftsByDate.has(day.iso) && unavailable.has(day.iso) ? 'calendar-cell-unavailable' : '')}
          onDayClick={(day) => {
            if (!day.inMonth) navigateWith({ date: day.iso });
            // Only future days without a shift can be toggled.
            else if (day.iso > data.today && !shiftsByDate.has(day.iso)) toggleUnavailability(day.iso);
          }}
          renderDay={(day) =>
            (shiftsByDate.get(day.iso) || []).map((shift) => (
              <div key={shift.id} className={`shift-chip mb-1 ${shiftTimeClass(shift)}`}>
                {shiftTimes(shift)} · {shift.position}
              </div>
            ))
          }
        />
      </div>
    </main>
  );
}
