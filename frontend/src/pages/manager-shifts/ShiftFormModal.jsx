import { useState } from 'react';

import { isUnavailable } from '../../app/shifts.js';
import { DateField, Field, PostForm, SelectField } from '../../components/Field.jsx';
import { FormFooter, Modal } from '../../components/Modal.jsx';
import { t } from '../../i18n/index.js';

// Typed 24-hour time with no picker widget; the browser checks the format, the server validates the value.
// Times read left to right in every language.
const timeInput = () => ({
  type: 'text',
  dir: 'ltr',
  inputMode: 'numeric',
  pattern: '([01][0-9]|2[0-3]):[0-5][0-9]',
  placeholder: 'HH:MM',
  maxLength: 5,
  title: t('shifts.timeFormat'),
  autoComplete: 'off',
});

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
  // A worked shift keeps no position once that position is deleted.
  const [positionId, setPositionId] = useState(String(shift.position_id ?? ''));
  const staff = employees.filter((employee) => String(employee.position_id) === positionId);

  return (
    <Modal
      title={isEdit ? t('shifts.editTitle') : t('shifts.createTitle')}
      onClose={onClose}
      maxWidth="45rem"
      footer={<FormFooter form="shiftForm" submitLabel={isEdit ? t('common.save') : t('shifts.create')} onCancel={onClose} />}
    >
      <PostForm id="shiftForm" className="modal-body" action={action} fields={isEdit ? { version: shift.version } : {}}>

        {stale ? (
          <p className="mb-3 text-sm text-destructive" role="alert">
            {t('shifts.stale')}
          </p>
        ) : editors.length ? (
          <p className="mb-3 text-sm text-muted-foreground" role="status">
            {t('shifts.alsoEditing', { names: editors.join(', '), count: editors.length })}
          </p>
        ) : null}

        <div className="grid grid-cols-2 gap-x-4">
          <DateField id="shiftDate" name="date" label={t('shifts.date')} required defaultValue={shift.date} onChange={setDate} />
          <Field id="shiftCapacity" name="capacity" type="number" min="1" label={t('shifts.capacity')} required defaultValue={shift.capacity} />
          <Field id="shiftStart" name="start_time" label={t('shifts.startTime')} required defaultValue={shift.start_time} {...timeInput()} />
          <Field id="shiftEnd" name="end_time" label={t('shifts.endTime')} required defaultValue={shift.end_time} {...timeInput()} />
        </div>

        <SelectField
          id="shiftPosition"
          name="position"
          label={t('shifts.position')}
          placeholder={t('shifts.selectPosition')}
          required
          options={positions}
          value={positionId}
          onChange={(event) => setPositionId(event.target.value)}
        />

        <fieldset>
          <legend className="form-label">{t('shifts.assignEmployees')}</legend>
          {staff.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {positionId ? t('shifts.noStaff') : t('shifts.selectPositionFirst')}
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
                    {unavailable ? <span className="availability-flag">{t('shifts.unavailable')}</span> : null}
                  </label>
                );
              })}
            </div>
          )}
        </fieldset>
      </PostForm>
    </Modal>
  );
}
