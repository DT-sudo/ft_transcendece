import { useEffect, useMemo, useRef, useState } from 'react';

import { formatDate, pad2 } from '../../app/dates.js';
import { submitPost, urlFromTemplate } from '../../app/http.js';
import { sendLive, useLiveEvents, useLivePageData } from '../../app/live.js';
import { availabilityFromPayload, positionPalette, shiftTimes, withAvailabilityChange } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { DeleteConfirmModal } from '../../components/Modal.jsx';
import { t } from '../../i18n/index.js';
import { EmployeeSidebar } from './EmployeeSidebar.jsx';
import { MonthGrid, WeekGrid } from './ShiftGrids.jsx';
import { ShiftDetailsModal } from './ShiftDetailsModal.jsx';
import { ShiftFormModal } from './ShiftFormModal.jsx';
import { ShiftsToolbar } from './ShiftsToolbar.jsx';

const FLASH_MS = 1600;

// A blank shift in the same shape the server sends, so the form handles create and edit alike.
const NEW_SHIFT = { date: '', start_time: '09:00', end_time: '17:00', capacity: 1, position_id: '', assigned_employee_ids: [] };

// A slot clicked in the week view pre-fills a one-hour shift from that hour.
const oneHourLater = (time) => `${pad2((Number(time.slice(0, 2)) + 1) % 24)}:00`;

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

/**
 * The other managers' calendars open right now, each with the month it shows and the
 * shift it is editing. This page announces its own month and edited shift the same way.
 */
function usePresence(month, editing) {
  const [others, setOthers] = useState({});
  const mine = useRef({ month, editing });
  const announce = (hello = false) => sendLive({ type: 'presence', ...mine.current, hello });

  // Declared before the subscription, so `mine` is current by the time the socket opens.
  useEffect(() => {
    mine.current = { month, editing };
    announce();
  }, [month, editing]);

  useLiveEvents(
    (event) => {
      if (event.type === 'presence') {
        setOthers((current) => ({ ...current, [event.id]: event }));
        if (event.hello) announce();
      } else if (event.type === 'presence.leave') {
        setOthers((current) => {
          const next = { ...current };
          delete next[event.id];
          return next;
        });
      }
    },
    {
      // A (re)connected page starts from nobody and asks everyone present to announce themselves.
      onOpen: () => {
        setOthers({});
        announce(true);
      },
    },
  );

  return Object.values(others);
}

/** Colour key for the calendar chips: the positions with published shifts this month, plus "Draft". */
function PositionLegend({ positions, shifts }) {
  const published = new Set(shifts.filter((shift) => shift.status !== 'draft').map((shift) => shift.position_id));

  return (
    <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs" aria-label={t('shifts.legend')}>
      {shifts.some((shift) => shift.status === 'draft') ? (
        <li className="inline-flex items-center gap-1.5">
          <span className="position-swatch position-swatch-draft" aria-hidden="true" />
          {t('status.draft')}
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
  const data = useLivePageData();

  return (
    <AppShell footer={<PositionLegend positions={data.positions} shifts={data.shifts} />}>
      <ManagerShiftsContent data={data} />
    </AppShell>
  );
}

function ManagerShiftsContent({ data }) {
  const { view, anchor, start, today, shifts, employees, positions, urls } = data;

  const [detailsShiftId, setDetailsShiftId] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [shiftForm, setShiftForm] = useState(null);
  // Clicking an employee in the sidebar outlines their shifts in both views; clicking again clears it.
  const [highlightedEmployeeId, setHighlightedEmployeeId] = useState(null);
  const highlightedShiftIds = useMemo(
    () => new Set(shifts.filter((shift) => shift.assigned_employee_ids.includes(highlightedEmployeeId)).map((shift) => shift.id)),
    [shifts, highlightedEmployeeId],
  );

  const { availability, flashedEmployeeId } = useLiveAvailability(data.unavailability);

  const editingId = shiftForm?.shift.id ?? null;
  const people = usePresence(anchor.slice(0, 7), editingId);
  const editors = {}; // shift id -> names of the other managers editing it
  for (const person of people) if (person.editing) (editors[person.editing] ??= []).push(person.name);
  // The live data no longer holds the version the form was opened on: someone else saved or deleted it.
  const stale = editingId !== null && shifts.find((shift) => shift.id === editingId)?.version !== shiftForm.shift.version;

  const detailsShift = shifts.find((shift) => shift.id === detailsShiftId) || null;
  const detailsNames = employees.filter((e) => detailsShift?.assigned_employee_ids.includes(e.id)).map((e) => e.name);

  const openCreateForm = (date = '', startTime = '') =>
    setShiftForm({
      shift: { ...NEW_SHIFT, date, ...(startTime && { start_time: startTime, end_time: oneHourLater(startTime) }) },
      action: urls.create,
    });

  const openEditForm = (shift) => {
    setDetailsShiftId(null);
    setShiftForm({ shift, action: urlFromTemplate(urls.update, shift.id) });
  };

  // Both views take the same shifts and the same handlers.
  const grid = {
    todayISO: today,
    shifts,
    editors,
    highlightedShiftIds,
    onSelectShift: setDetailsShiftId,
    onCreateSlot: openCreateForm,
  };

  return (
    <>
      <main className="p-4 pt-0">
        <ShiftsToolbar data={data} onCreateShift={() => openCreateForm()} />

        <div className="manager-calendar-layout">
          <EmployeeSidebar
            employees={employees}
            flashedEmployeeId={flashedEmployeeId}
            highlightedEmployeeId={highlightedEmployeeId}
            onToggleEmployee={(id) => setHighlightedEmployeeId((current) => (current === id ? null : id))}
          />

          <div className="card calendar-fill mt-3">
            {view === 'week' ? <WeekGrid startISO={start} {...grid} /> : <MonthGrid anchorISO={anchor} {...grid} />}
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
          stale={stale}
          editors={editors[editingId] || []}
          onClose={() => setShiftForm(null)}
        />
      ) : null}

      {detailsShift ? (
        <ShiftDetailsModal
          shift={detailsShift}
          assignedNames={detailsNames}
          editors={editors[detailsShift.id] || []}
          onClose={() => setDetailsShiftId(null)}
          onEdit={() => openEditForm(detailsShift)}
          onPublish={() => submitPost(urlFromTemplate(urls.publish, detailsShift.id))}
          onDelete={() =>
            setPendingDelete({
              id: detailsShift.id,
              label: `${detailsShift.position} • ${shiftTimes(detailsShift)} • ${formatDate(detailsShift.date)}`,
            })
          }
        />
      ) : null}

      {pendingDelete ? (
        <DeleteConfirmModal
          title={t('shifts.deleteTitle')}
          message={t('shifts.deleteMessage')}
          detail={pendingDelete.label}
          action={urlFromTemplate(urls.delete, pendingDelete.id)}
          onCancel={() => setPendingDelete(null)}
        />
      ) : null}
    </>
  );
}
