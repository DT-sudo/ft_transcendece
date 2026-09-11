import { useEffect, useRef, useState } from 'react';

import { formatDate } from '../../app/dates.js';
import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { useLiveEvents } from '../../app/live.js';
import { availabilityFromPayload, withAvailabilityChange } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { useToast } from '../../components/Toasts.jsx';
import { EmployeeSidebar } from './EmployeeSidebar.jsx';
import { MonthGrid } from './ShiftGrids.jsx';
import { ShiftDetailsModal } from './ShiftDetailsModal.jsx';
import { ShiftFormModal } from './ShiftFormModal.jsx';
import { ShiftsToolbar } from './ShiftsToolbar.jsx';

const FLASH_MS = 1600;

// A blank shift in the same shape the server sends, so the form handles create and edit alike.
const NEW_SHIFT = { date: '', start_time: '09:00', end_time: '17:00', capacity: 1, position_id: '', assigned_employee_ids: [] };

/** Employees' unavailable days, updated live when an employee changes them. */
function useLiveAvailability(initial) {
  const showToast = useToast();
  const [availability, setAvailability] = useState(() => availabilityFromPayload(initial));
  const [flashedEmployeeId, setFlashedEmployeeId] = useState(null);
  const flashTimer = useRef(null);

  useEffect(() => () => clearTimeout(flashTimer.current), []);

  const status = useLiveEvents(
    (event) => {
      if (event.type !== 'unavailability.changed') return;

      setAvailability((current) => withAvailabilityChange(current, event));

      clearTimeout(flashTimer.current);
      setFlashedEmployeeId(String(event.employeeId));
      flashTimer.current = setTimeout(() => setFlashedEmployeeId(null), FLASH_MS);

      showToast(
        'info',
        'Availability updated',
        `${event.employeeName} is ${event.unavailable ? 'unavailable' : 'available again'} on ${formatDate(event.date)}.`,
      );
    },
    {
      onReconnect: () =>
        showToast('warning', 'Live updates restored', 'Reload to see changes made while you were offline.'),
    },
  );

  return { availability, flashedEmployeeId, status };
}

export function ManagerShiftsPage() {
  return (
    <AppShell>
      <ManagerShiftsContent />
    </AppShell>
  );
}

function ManagerShiftsContent() {
  const { data } = getBootstrap();
  const { anchor, start, end, today, shifts, employees, positions, urls } = data;

  const [detailsShiftId, setDetailsShiftId] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [shiftForm, setShiftForm] = useState(null);

  // A page restored from the back/forward cache would show stale shifts.
  useEffect(() => {
    const onPageShow = (event) => event.persisted && window.location.reload();
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  }, []);
  const { availability, flashedEmployeeId, status: liveStatus } = useLiveAvailability(data.unavailability);

  const detailsShift = shifts.find((shift) => shift.id === detailsShiftId) || null;
  const detailsNames = employees.filter((e) => detailsShift?.assigned_employee_ids.includes(e.id)).map((e) => e.name);

  const openCreateForm = (date = '') => setShiftForm({ shift: { ...NEW_SHIFT, date }, action: urls.create });

  const openEditForm = (shift) => {
    setDetailsShiftId(null);
    setShiftForm({ shift, action: urlFromTemplate(urls.update, shift.id) });
  };

  return (
    <>
      <main className="p-4 pt-0">
        <ShiftsToolbar data={data} onCreateShift={() => openCreateForm()} />

        <div className="manager-calendar-layout">
          <EmployeeSidebar
            employees={employees}
            availability={availability}
            periodStart={start}
            periodEnd={end}
            flashedEmployeeId={flashedEmployeeId}
            liveStatus={liveStatus}
          />

          <div className="card manager-calendar-fill mt-3">
            <MonthGrid
              anchorISO={anchor}
              todayISO={today}
              shifts={shifts}
              onSelectShift={setDetailsShiftId}
              onCreateSlot={openCreateForm}
            />
          </div>
        </div>
      </main>

      {shiftForm ? (
        <ShiftFormModal
          shift={shiftForm.shift}
          action={shiftForm.action}
          positions={positions}
          employees={employees}
          availability={availability}
          onClose={() => setShiftForm(null)}
        />
      ) : null}

      {detailsShift ? (
        <ShiftDetailsModal
          shift={detailsShift}
          assignedNames={detailsNames}
          onClose={() => setDetailsShiftId(null)}
          onEdit={() => openEditForm(detailsShift)}
          onPublish={() => submitPost(urlFromTemplate(urls.publish, detailsShift.id))}
          onDelete={() =>
            setPendingDelete({
              id: detailsShift.id,
              label: `${detailsShift.position} • ${detailsShift.start_time}-${detailsShift.end_time} • ${detailsShift.date}`,
            })
          }
        />
      ) : null}

      {pendingDelete ? (
        <ConfirmModal
          title="Delete shift"
          message="Delete this shift:"
          detail={pendingDelete.label}
          confirmText="Yes, delete"
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.delete, pendingDelete.id))}
        />
      ) : null}
    </>
  );
}
