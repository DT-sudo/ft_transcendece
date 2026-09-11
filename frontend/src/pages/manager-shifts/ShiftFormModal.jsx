import { useState } from 'react';

import { isUnavailable } from '../../app/shifts.js';
import { CsrfInput, Field, SelectField } from '../../components/Field.jsx';
import { Modal } from '../../components/Modal.jsx';

/**
 * Create/edit shift form over a shift in the server's payload shape (a blank one when creating).
 * Submits natively; the server enforces every scheduling rule.
 */
export function ShiftFormModal({ shift, action, positions, employees, availability, onClose }) {
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

        <div className="grid grid-cols-2 gap-x-4">
          <Field id="shiftDate" name="date" type="date" label="Date" required value={date} onChange={(event) => setDate(event.target.value)} />
          <Field id="shiftCapacity" name="capacity" type="number" min="1" label="Capacity" required defaultValue={shift.capacity} />
          <Field id="shiftStart" name="start_time" type="time" label="Start time" required defaultValue={shift.start_time} />
          <Field id="shiftEnd" name="end_time" type="time" label="End time" required defaultValue={shift.end_time} />
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
