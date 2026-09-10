import { useEffect, useMemo, useState } from 'react';

import { isUnavailable } from '../../app/shifts.js';
import { Modal } from '../../components/Modal.jsx';
import { SelectPopover } from '../../components/Menus.jsx';
import { CsrfInput } from '../../components/Field.jsx';
import { useToast } from '../../components/Toasts.jsx';

const FORM_ID = 'shiftForm';

function EmployeeChips({ employees, selectedIds, unavailableIds, onRemove, hasPosition }) {
  if (!selectedIds.length) {
    return (
      <span className="text-muted-foreground">
        {hasPosition ? 'Select employees' : 'Select position first'}
      </span>
    );
  }

  return (
    <span className="flex min-h-5 flex-auto flex-wrap items-center gap-1.5">
      {selectedIds.map((id) => {
        const employee = employees.find((item) => String(item.id) === String(id));
        const name = employee?.name || 'Employee';
        const unavailable = unavailableIds.has(String(id));

        return (
          <span className={`tag-chip ${unavailable ? 'tag-chip-warning' : ''}`} key={id}>
            <span
              className="chip-remove"
              role="button"
              tabIndex={0}
              aria-label={`Remove ${name}`}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                onRemove(id);
              }}
              onKeyDown={(event) => {
                if (event.key !== 'Enter' && event.key !== ' ') return;
                event.preventDefault();
                event.stopPropagation();
                onRemove(id);
              }}
            >
              x
            </span>
            <span className="whitespace-nowrap">
              {name}
              {unavailable ? ' (unavailable)' : ''}
            </span>
          </span>
        );
      })}
    </span>
  );
}

/** Create/edit shift form. Submits natively so the server keeps owning the rules. */
export function ShiftFormModal({ mode, initial, positions, employees, availability, action, returnView, onClose }) {
  const showToast = useToast();
  const [form, setForm] = useState(initial);

  useEffect(() => setForm(initial), [initial]);

  const setField = (name, value) => setForm((current) => ({ ...current, [name]: value }));

  const positionEmployees = useMemo(
    () => employees.filter((employee) => String(employee.position_id ?? '') === String(form.positionId ?? '')),
    [employees, form.positionId],
  );

  // Recomputed whenever the date changes or an employee updates their availability live.
  const unavailableIds = useMemo(
    () =>
      new Set(
        employees
          .filter((employee) => isUnavailable(availability, employee.id, form.date))
          .map((employee) => String(employee.id)),
      ),
    [employees, availability, form.date],
  );

  const availableEmployees = positionEmployees.filter((employee) => !unavailableIds.has(String(employee.id)));
  const unavailableSelectedNames = form.employeeIds
    .filter((id) => unavailableIds.has(String(id)))
    .map((id) => employees.find((employee) => String(employee.id) === String(id))?.name || 'Employee');

  const selectedPosition = positions.find((position) => String(position.id) === String(form.positionId));

  const setPosition = (positionId) => {
    setForm((current) => ({
      ...current,
      positionId,
      // An employee only qualifies for one position, so the picks cannot carry over.
      employeeIds: String(current.positionId ?? '') === String(positionId) ? current.employeeIds : [],
    }));
  };

  const toggleEmployee = (id, checked) => {
    setForm((current) => {
      const ids = current.employeeIds.filter((value) => String(value) !== String(id));
      return { ...current, employeeIds: checked ? [...ids, String(id)] : ids };
    });
  };

  const handleSubmit = (event) => {
    if (form.startTime && form.endTime && form.startTime >= form.endTime) {
      event.preventDefault();
      showToast('error', 'Invalid time range', 'End time must be after start time.');
      return;
    }
    // Mirrors the server's availability rule; the server still rejects it on its own.
    if (unavailableSelectedNames.length) {
      event.preventDefault();
      showToast('error', 'Employee unavailable', `${unavailableSelectedNames.join(', ')} cannot work on this date.`);
    }
  };

  return (
    <Modal
      title={mode === 'edit' ? 'Edit Shift' : 'Create Shift'}
      onClose={onClose}
      maxWidth="720px"
      className="modal-overflow-visible"
      footer={
        <>
          <button className="btn btn-outline" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" type="submit" form={FORM_ID}>
            {mode === 'edit' ? 'Save' : 'Create Shift'}
          </button>
        </>
      }
    >
      <div className="modal-body">
        <form id={FORM_ID} method="post" action={action} onSubmit={handleSubmit}>
          <CsrfInput />
          <input type="hidden" name="return_view" value={returnView} readOnly />
          <input type="hidden" name="position" value={form.positionId ?? ''} readOnly />
          {form.employeeIds.map((id) => (
            <input key={id} type="hidden" name="employee_ids" value={id} readOnly />
          ))}

          <div className="flex gap-4">
            <div className="mb-4 flex-1">
              <label className="form-label" htmlFor="shiftDate">
                Date *
              </label>
              <input
                type="date"
                className="form-input"
                id="shiftDate"
                name="date"
                required
                value={form.date}
                onChange={(event) => setField('date', event.target.value)}
              />
            </div>
            <div className="mb-4 flex-1">
              <label className="form-label" htmlFor="shiftCapacity">
                Capacity *
              </label>
              <input
                type="number"
                className="form-input"
                id="shiftCapacity"
                name="capacity"
                min="1"
                required
                value={form.capacity}
                onChange={(event) => setField('capacity', event.target.value)}
              />
            </div>
          </div>

          <div className="flex gap-4">
            <div className="mb-4 flex-1">
              <label className="form-label" htmlFor="shiftStart">
                Start Time *
              </label>
              <input
                type="time"
                className="form-input"
                id="shiftStart"
                name="start_time"
                required
                value={form.startTime}
                onChange={(event) => setField('startTime', event.target.value)}
              />
            </div>
            <div className="mb-4 flex-1">
              <label className="form-label" htmlFor="shiftEnd">
                End Time *
              </label>
              <input
                type="time"
                className="form-input"
                id="shiftEnd"
                name="end_time"
                required
                value={form.endTime}
                onChange={(event) => setField('endTime', event.target.value)}
              />
            </div>
          </div>
        </form>

        <div className="mb-4">
          <span className="form-label">Position *</span>
          <SelectPopover
            full
            ariaLabel="Select position"
            menuClassName="multiselect-menu-scroll"
            label={<span>{selectedPosition ? selectedPosition.name : 'Select position...'}</span>}
          >
            {({ close }) =>
              positions.length ? (
                positions.map((position) => (
                  <label className="multiselect-item" key={position.id}>
                    <input
                      type="radio"
                      name="shiftPositionChoice"
                      value={position.id}
                      checked={String(form.positionId ?? '') === String(position.id)}
                      onChange={() => {
                        setPosition(String(position.id));
                        close();
                      }}
                    />
                    {position.name}
                  </label>
                ))
              ) : (
                <div className="px-3 py-2 text-sm text-muted-foreground">No positions yet.</div>
              )
            }
          </SelectPopover>
        </div>

        <div>
          <span className="form-label">Assign Employees</span>
          <SelectPopover
            full
            ariaLabel="Select employees"
            label={
              <EmployeeChips
                employees={employees}
                selectedIds={form.employeeIds}
                unavailableIds={unavailableIds}
                hasPosition={Boolean(form.positionId)}
                onRemove={(id) => toggleEmployee(id, false)}
              />
            }
          >
            {() => (
              <>
                {!form.positionId ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">Select position first</div>
                ) : positionEmployees.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    No employees for this position
                  </div>
                ) : (
                  <div className="max-h-70 overflow-y-auto">
                    {positionEmployees.map((employee) => {
                      const checked = form.employeeIds.some((id) => String(id) === String(employee.id));
                      const unavailable = unavailableIds.has(String(employee.id));

                      return (
                        <label
                          className={`multiselect-item ${unavailable ? 'multiselect-item-disabled' : ''}`}
                          key={employee.id}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            // Still clickable when already picked, so the pick can be removed.
                            disabled={unavailable && !checked}
                            onChange={(event) => toggleEmployee(employee.id, event.target.checked)}
                          />
                          <span className="min-w-0 flex-auto truncate">{employee.name}</span>
                          {unavailable ? <span className="availability-flag">Unavailable</span> : null}
                        </label>
                      );
                    })}
                  </div>
                )}

                <div className="multiselect-actions">
                  <button
                    className="btn btn-ghost btn-sm"
                    type="button"
                    disabled={!availableEmployees.length}
                    onClick={() =>
                      setForm((current) => ({
                        ...current,
                        employeeIds: availableEmployees.map((employee) => String(employee.id)),
                      }))
                    }
                  >
                    Select all
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    type="button"
                    onClick={() => setForm((current) => ({ ...current, employeeIds: [] }))}
                  >
                    Clear
                  </button>
                </div>
              </>
            )}
          </SelectPopover>

          {unavailableSelectedNames.length ? (
            <p className="form-error-text mt-1.5" role="alert">
              {unavailableSelectedNames.join(', ')} {unavailableSelectedNames.length === 1 ? 'is' : 'are'}{' '}
              unavailable on this date. Remove them before saving.
            </p>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
