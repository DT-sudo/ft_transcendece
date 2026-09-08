import { useEffect, useMemo, useState } from 'react';

import { Modal } from '../../components/Modal.jsx';
import { SelectPopover } from '../../components/Menus.jsx';
import { CsrfInput } from '../../components/PostForm.jsx';
import { useToast } from '../../components/Toasts.jsx';

const FORM_ID = 'shiftForm';

function EmployeeChips({ employees, selectedIds, onRemove, hasPosition }) {
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

        return (
          <span className="tag-chip" key={id}>
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
            <span className="whitespace-nowrap">{name}</span>
          </span>
        );
      })}
    </span>
  );
}

/** Create/edit shift form. Submits natively so the server keeps owning the rules. */
export function ShiftFormModal({ mode, initial, positions, employees, action, returnView, onClose }) {
  const showToast = useToast();
  const [form, setForm] = useState(initial);

  useEffect(() => setForm(initial), [initial]);

  const setField = (name, value) => setForm((current) => ({ ...current, [name]: value }));

  const positionEmployees = useMemo(
    () => employees.filter((employee) => String(employee.position_id ?? '') === String(form.positionId ?? '')),
    [employees, form.positionId],
  );

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
          <input type="hidden" name="position_id" value={form.positionId ?? ''} readOnly />
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
                    {positionEmployees.map((employee) => (
                      <label className="multiselect-item" key={employee.id}>
                        <input
                          type="checkbox"
                          checked={form.employeeIds.some((id) => String(id) === String(employee.id))}
                          onChange={(event) => toggleEmployee(employee.id, event.target.checked)}
                        />
                        {employee.name}
                      </label>
                    ))}
                  </div>
                )}

                <div className="multiselect-actions">
                  <button
                    className="btn btn-ghost btn-sm"
                    type="button"
                    disabled={!positionEmployees.length}
                    onClick={() =>
                      setForm((current) => ({
                        ...current,
                        employeeIds: positionEmployees.map((employee) => String(employee.id)),
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
        </div>
      </div>
    </Modal>
  );
}
