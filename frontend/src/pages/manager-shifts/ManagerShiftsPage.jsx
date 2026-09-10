import { useEffect, useMemo, useRef, useState } from 'react';

import { formatDate, pad2 } from '../../app/dates.js';
import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { useLiveEvents } from '../../app/live.js';
import {
  availabilityFromPayload,
  employeePeriodStats,
  positionPalette,
  withAvailabilityChange,
} from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { useToast } from '../../components/Toasts.jsx';
import { useReloadOnBackForward } from '../../components/hooks.js';
import { EmployeeSidebar } from './EmployeeSidebar.jsx';
import { MonthGrid, WeekGrid } from './ShiftGrids.jsx';
import { ShiftDetailsModal } from './ShiftDetailsModal.jsx';
import { ShiftFormModal } from './ShiftFormModal.jsx';
import { ShiftsToolbar } from './ShiftsToolbar.jsx';

const FLASH_MS = 1600;

/** Fixed bottom bar listing the position colours present in the period, plus "Draft" when relevant. */
function PositionLegend({ positions, shifts }) {
  const usedPositionIds = new Set(shifts.filter((shift) => shift.status !== 'draft').map((shift) => shift.position_id));

  return (
    <div className="legend-bar">
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 overflow-hidden" aria-label="Position color legend">
        {shifts.some((shift) => shift.status === 'draft') ? (
          <div className="inline-flex items-center gap-2 text-sm">
            <span className="position-swatch position-swatch-draft" aria-hidden="true" />
            <span>Draft</span>
          </div>
        ) : null}

        {positions
          .filter((position) => usedPositionIds.has(position.id))
          .map((position) => (
            <div className="inline-flex items-center gap-2 text-sm" key={position.id}>
              <span className="position-swatch" style={positionPalette(position.id)} aria-hidden="true" />
              <span>{position.name}</span>
            </div>
          ))}
      </div>
    </div>
  );
}

const EMPTY_FORM = {
  date: '',
  startTime: '09:00',
  endTime: '17:00',
  capacity: '1',
  positionId: '',
  employeeIds: [],
};

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

function nextHour(hour) {
  const [hours, minutes] = String(hour || '').split(':').map(Number);
  if (!Number.isFinite(hours)) return '';
  return `${pad2((hours + 1) % 24)}:${pad2(Number.isFinite(minutes) ? minutes : 0)}`;
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
  const { view, anchor, start, end, today, shifts, employees, positions, urls } = data;

  const [activeEmployeeId, setActiveEmployeeId] = useState(null);
  const [detailsShiftId, setDetailsShiftId] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [shiftForm, setShiftForm] = useState(null);

  useReloadOnBackForward();
  const { availability, flashedEmployeeId, status: liveStatus } = useLiveAvailability(data.unavailability);

  const stats = useMemo(() => employeePeriodStats(shifts), [shifts]);
  const employeesById = useMemo(
    () => new Map(employees.map((employee) => [String(employee.id), employee])),
    [employees],
  );

  const highlightedShiftIds = useMemo(
    () => (activeEmployeeId ? stats.shiftIdsByEmployee.get(activeEmployeeId) ?? new Set() : new Set()),
    [activeEmployeeId, stats],
  );

  const detailsShift = shifts.find((shift) => String(shift.id) === String(detailsShiftId)) || null;
  const detailsEmployees = (detailsShift?.assigned_employee_ids || []).map((id) => ({
    id,
    name: employeesById.get(String(id))?.name || `Employee #${id}`,
  }));

  const openCreateForm = (date = '', startTime = '') =>
    setShiftForm({
      mode: 'create',
      action: urls.create,
      initial: {
        ...EMPTY_FORM,
        date,
        startTime: startTime || EMPTY_FORM.startTime,
        endTime: startTime ? nextHour(startTime) : EMPTY_FORM.endTime,
      },
    });

  const openEditForm = (shift) => {
    setDetailsShiftId(null);
    setShiftForm({
      mode: 'edit',
      action: urlFromTemplate(urls.update, shift.id),
      initial: {
        date: shift.date,
        startTime: shift.start_time,
        endTime: shift.end_time,
        capacity: String(shift.capacity ?? 1),
        positionId: String(shift.position_id ?? ''),
        employeeIds: (shift.assigned_employee_ids || []).map(String),
      },
    });
  };

  const gridProps = {
    shifts,
    todayISO: today,
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
            positions={positions}
            minutesByEmployee={stats.minutesByEmployee}
            availability={availability}
            periodStart={start}
            periodEnd={end}
            flashedEmployeeId={flashedEmployeeId}
            liveStatus={liveStatus}
            activeEmployeeId={activeEmployeeId}
            onToggleEmployee={(id) => setActiveEmployeeId((current) => (current === id ? null : id))}
          />

          <div className="card manager-calendar-fill mt-3">
            {view === 'month' ? (
              <MonthGrid anchorISO={anchor} {...gridProps} />
            ) : (
              <WeekGrid startISO={start} {...gridProps} />
            )}
          </div>
        </div>
      </main>

      <PositionLegend positions={positions} shifts={shifts} />

      {shiftForm ? (
        <ShiftFormModal
          mode={shiftForm.mode}
          action={shiftForm.action}
          initial={shiftForm.initial}
          positions={positions}
          employees={employees}
          availability={availability}
          returnView={view}
          onClose={() => setShiftForm(null)}
        />
      ) : null}

      {detailsShift ? (
        <ShiftDetailsModal
          shift={detailsShift}
          assignedEmployees={detailsEmployees}
          onClose={() => setDetailsShiftId(null)}
          onEdit={() => openEditForm(detailsShift)}
          onPublish={() => submitPost(urlFromTemplate(urls.publish, detailsShift.id), { return_view: view })}
          onDelete={() =>
            setPendingDelete({
              id: detailsShift.id,
              label:
                [
                  detailsShift.position,
                  `${detailsShift.start_time}-${detailsShift.end_time}`,
                  detailsShift.date,
                ]
                  .filter(Boolean)
                  .join(' • ') || `#${detailsShift.id}`,
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
