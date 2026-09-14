import { useEffect, useRef, useState } from 'react';

import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { useLiveEvents, useLivePageData } from '../../app/live.js';
import { availabilityFromPayload, positionPalette, withAvailabilityChange } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { EmployeeSidebar } from './EmployeeSidebar.jsx';
import { MonthGrid } from './ShiftGrids.jsx';
import { ShiftDetailsModal } from './ShiftDetailsModal.jsx';
import { ShiftFormModal } from './ShiftFormModal.jsx';
import { ShiftsToolbar } from './ShiftsToolbar.jsx';

const FLASH_MS = 1600;

// A blank shift in the same shape the server sends, so the form handles create and edit alike.
const NEW_SHIFT = { date: '', start_time: '09:00', end_time: '17:00', capacity: 1, position_id: '', assigned_employee_ids: [] };

/** Employees' unavailable days, updated live when an employee changes them (the bell raises the toast). */
function useLiveAvailability(initial) {
  const [availability, setAvailability] = useState(() => availabilityFromPayload(initial));
  const [flashedEmployeeId, setFlashedEmployeeId] = useState(null);
  const flashTimer = useRef(null);

  useEffect(() => () => clearTimeout(flashTimer.current), []);

  useLiveEvents((event) => {
    if (event.type !== 'unavailability.changed') return;

    setAvailability((current) => withAvailabilityChange(current, event));

    clearTimeout(flashTimer.current);
    setFlashedEmployeeId(String(event.employeeId));
    flashTimer.current = setTimeout(() => setFlashedEmployeeId(null), FLASH_MS);
  });

  return { availability, flashedEmployeeId };
}

/** Colour key for the calendar chips: the positions with published shifts this month, plus "Draft". */
function PositionLegend({ positions, shifts }) {
  const published = new Set(shifts.filter((shift) => shift.status !== 'draft').map((shift) => shift.position_id));

  return (
    <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs" aria-label="Position colours">
      {shifts.some((shift) => shift.status === 'draft') ? (
        <li className="inline-flex items-center gap-1.5">
          <span className="position-swatch position-swatch-draft" aria-hidden="true" />
          Draft
        </li>
      ) : null}
      {positions
        .filter((position) => published.has(position.id))
        .map((position) => (
          <li key={position.id} className="inline-flex items-center gap-1.5">
            <span className="position-swatch position-color" style={positionPalette(position.id)} aria-hidden="true" />
            {position.name}
          </li>
        ))}
    </ul>
  );
}

export function ManagerShiftsPage() {
  const data = useLivePageData(getBootstrap().data);

  return (
    <AppShell footer={<PositionLegend positions={data.positions} shifts={data.shifts} />}>
      <ManagerShiftsContent data={data} />
    </AppShell>
  );
}

function ManagerShiftsContent({ data }) {
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
  const { availability, flashedEmployeeId } = useLiveAvailability(data.unavailability);

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
          />

          <div className="card calendar-fill mt-3">
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
