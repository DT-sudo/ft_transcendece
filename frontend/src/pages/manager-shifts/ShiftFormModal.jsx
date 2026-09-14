import { useState } from 'react';

import { isUnavailable } from '../../app/shifts.js';
import { CsrfInput, Field, SelectField } from '../../components/Field.jsx';
import { Modal } from '../../components/Modal.jsx';

// Typed 24-hour time with no picker widget; the browser checks the format, the server validates the value.
const TIME_INPUT = {
  type: 'text',
  inputMode: 'numeric',
  pattern: '([01][0-9]|2[0-3]):[0-5][0-9]',
  placeholder: 'HH:MM',
  maxLength: 5,
  title: '24-hour time, e.g. 09:30',
  autoComplete: 'off',
};

/**
 * Create/edit shift form over a shift in the server's payload shape (a blank one when creating).
 * Submits natively; the server enforces every scheduling rule, and refuses an edit whose
 * `version` is no longer current. `stale` warns about that ahead of time; `editors` are the
 * other managers who have the same shift open.
 */
export function ShiftFormModal({ shift, action, positions, employees, availability, stale, editors, onClose }) {
  const isEdit = Boolean(shift.id);
  // Only the two fields that change what the form shows are tracked; the rest submit as typed.
  const [date, setDate] = useState(shift.date);
  const [positionId, setPositionId] = useState(String(shift.position_id));
  const staff = employees.filter((employee) => String(employee.position_id) === positionId);

  return (
    <Modal
      title={isEdit ? 'Edit Shift' : 'Create Shift'}
      onClose={onClose}
      maxWidth="720px"
      footer={
        <>
          <button className="btn btn-outline" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" type="submit" form="shiftForm">
            {isEdit ? 'Save' : 'Create Shift'}
          </button>
        </>
      }
    >
      <form id="shiftForm" className="modal-body" method="post" action={action}>
        <CsrfInput />
        {isEdit ? <input type="hidden" name="version" value={shift.version} readOnly /> : null}

        {stale ? (
          <p className="mb-3 text-sm text-destructive" role="alert">
            Someone else just changed or deleted this shift, so saving will be refused. Close and reopen it to see the
            latest version.
          </p>
        ) : editors.length ? (
          <p className="mb-3 text-sm text-muted-foreground" role="status">
            {editors.join(', ')} {editors.length === 1 ? 'is' : 'are'} also editing this shift.
          </p>
        ) : null}

        <div className="grid grid-cols-2 gap-x-4">
          <Field id="shiftDate" name="date" type="date" label="Date" required value={date} onChange={(event) => setDate(event.target.value)} />
          <Field id="shiftCapacity" name="capacity" type="number" min="1" label="Capacity" required defaultValue={shift.capacity} />
          <Field id="shiftStart" name="start_time" label="Start time" required defaultValue={shift.start_time} {...TIME_INPUT} />
          <Field id="shiftEnd" name="end_time" label="End time" required defaultValue={shift.end_time} {...TIME_INPUT} />
        </div>

        <SelectField
          id="shiftPosition"
          name="position"
          label="Position"
          placeholder="Select position..."
          required
          options={positions}
          value={positionId}
          onChange={(event) => setPositionId(event.target.value)}
        />

        <fieldset>
          <legend className="form-label">Assign employees</legend>
          {staff.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {positionId ? 'No employees for this position.' : 'Select a position first.'}
            </p>
          ) : (
            <div className="max-h-56 overflow-y-auto rounded-card border border-border p-1">
              {staff.map((employee) => {
                // Unavailable employees can't be picked; an existing pick stays so the server explains the conflict.
                const assigned = shift.assigned_employee_ids.includes(employee.id);
                const unavailable = isUnavailable(availability, employee.id, date);
                return (
                  <label className="multiselect-item" key={employee.id}>
                    <input type="checkbox" name="employee_ids" value={employee.id} defaultChecked={assigned} disabled={unavailable && !assigned} />
                    <span className="min-w-0 flex-auto truncate">{employee.name}</span>
                    {unavailable ? <span className="availability-flag">Unavailable</span> : null}
                  </label>
                );
              })}
            </div>
          )}
        </fieldset>
      </form>
    </Modal>
  );
}
