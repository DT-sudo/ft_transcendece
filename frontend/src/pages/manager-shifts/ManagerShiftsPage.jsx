import { useLayoutEffect, useMemo, useRef, useState } from 'react';

import { getBootstrap } from '../../app/bootstrap.js';
import { pad2 } from '../../app/dates.js';
import { urlFromTemplate } from '../../app/http.js';
import { employeePeriodStats } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { PostForm } from '../../components/PostForm.jsx';
import { useOnResize, useReloadOnBackForward } from '../../components/hooks.js';
import { EmployeeSidebar } from './EmployeeSidebar.jsx';
import { MonthGrid } from './MonthGrid.jsx';
import { PositionLegend } from './PositionLegend.jsx';
import { ShiftDetailsModal } from './ShiftDetailsModal.jsx';
import { ShiftFormModal } from './ShiftFormModal.jsx';
import { ShiftsToolbar } from './ShiftsToolbar.jsx';
import { WeekGrid } from './WeekGrid.jsx';

const VIEW_CARD_MARGIN_PX = 12;
const MIN_CALENDAR_HEIGHT_PX = 320;

const EMPTY_FORM = {
  date: '',
  startTime: '09:00',
  endTime: '17:00',
  capacity: '1',
  positionId: '',
  employeeIds: [],
};

/** Sidebar and calendar fill the space left between the toolbar and the legend bar. */
function useCalendarFillHeight(toolbarRef) {
  const sync = () => {
    const root = document.documentElement;
    const headerHeight = document.querySelector('header')?.getBoundingClientRect().height || 0;
    const toolbarHeight = toolbarRef.current?.getBoundingClientRect().height || 0;
    root.style.setProperty('--toolbar-sticky-height', `${toolbarHeight}px`);

    const legendHeight = parseFloat(getComputedStyle(root).getPropertyValue('--legend-bar-height')) || 0;
    const available =
      window.innerHeight - headerHeight - toolbarHeight - legendHeight - VIEW_CARD_MARGIN_PX * 2;

    root.style.setProperty(
      '--manager-calendar-fill-height',
      `${Math.max(MIN_CALENDAR_HEIGHT_PX, Math.floor(available))}px`,
    );
  };

  useLayoutEffect(() => {
    const observer = new ResizeObserver(sync);
    if (toolbarRef.current) observer.observe(toolbarRef.current);

    const header = document.querySelector('header');
    if (header) observer.observe(header);

    sync();
    return () => observer.disconnect();
  }, []);

  useOnResize(sync);
}

function nextHour(hour) {
  const [hours, minutes] = String(hour || '').split(':').map(Number);
  if (!Number.isFinite(hours)) return '';
  return `${pad2((hours + 1) % 24)}:${pad2(Number.isFinite(minutes) ? minutes : 0)}`;
}

export function ManagerShiftsPage() {
  const { data } = getBootstrap();
  const { view, anchor, start, today, shifts, employees, positions, urls } = data;

  const toolbarRef = useRef(null);
  const deleteFormRef = useRef(null);
  const publishFormRef = useRef(null);

  const [activeEmployeeId, setActiveEmployeeId] = useState(null);
  const [detailsShiftId, setDetailsShiftId] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [shiftForm, setShiftForm] = useState(null);

  useCalendarFillHeight(toolbarRef);
  useReloadOnBackForward();

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

  const submitPublish = () => {
    if (!detailsShift) return;
    publishFormRef.current.action = urlFromTemplate(urls.publish, detailsShift.id);
    publishFormRef.current.submit();
  };

  const submitDelete = () => {
    if (!pendingDelete) return;
    deleteFormRef.current.action = urlFromTemplate(urls.delete, pendingDelete.id);
    deleteFormRef.current.submit();
  };

  const gridProps = {
    shifts,
    todayISO: today,
    highlightedShiftIds,
    onSelectShift: setDetailsShiftId,
    onCreateSlot: openCreateForm,
  };

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <ShiftsToolbar ref={toolbarRef} data={data} onCreateShift={() => openCreateForm()} />

        <div className="manager-calendar-layout">
          <EmployeeSidebar
            employees={employees}
            positions={positions}
            minutesByEmployee={stats.minutesByEmployee}
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

      <PostForm formRef={deleteFormRef} action={urls.delete} />
      <PostForm formRef={publishFormRef} action={urls.publish} fields={{ return_view: view }} />

      {shiftForm ? (
        <ShiftFormModal
          mode={shiftForm.mode}
          action={shiftForm.action}
          initial={shiftForm.initial}
          positions={positions}
          employees={employees}
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
          onPublish={submitPublish}
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
          onConfirm={submitDelete}
        />
      ) : null}
    </AppShell>
  );
}
