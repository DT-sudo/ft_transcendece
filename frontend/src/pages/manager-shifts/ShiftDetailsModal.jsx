import { formatDate, formatDuration, shiftDurationMinutes } from '../../app/dates.js';
import { Modal } from '../../components/Modal.jsx';
import { ShiftStatusBadge } from '../../components/ShiftStatusBadge.jsx';

export function ShiftDetailsModal({ shift, assignedNames, editors, onClose, onEdit, onDelete, onPublish }) {
  const isDraft = shift.status === 'draft';

  return (
    <Modal
      title="Shift Details"
      onClose={onClose}
      titleExtra={<ShiftStatusBadge status={shift.status} />}
      footer={
        <>
          <button className="btn btn-destructive" type="button" onClick={onDelete}>
            Delete
          </button>
          {isDraft ? (
            <button className="btn btn-primary" type="button" onClick={onPublish}>
              Publish
            </button>
          ) : null}
          <button className="btn btn-outline" type="button" onClick={onEdit}>
            Edit
          </button>
        </>
      }
    >
      <dl className="modal-body grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
        <dt className="text-muted-foreground">Date</dt>
        <dd>{formatDate(shift.date)}</dd>
        <dt className="text-muted-foreground">Time</dt>
        <dd>
          {shift.start_time}-{shift.end_time} ({formatDuration(shiftDurationMinutes(shift))})
        </dd>
        <dt className="text-muted-foreground">Position</dt>
        <dd>{shift.position}</dd>
        <dt className="text-muted-foreground">Staffed</dt>
        <dd>
          {shift.assigned_employee_ids.length}/{shift.capacity}
        </dd>
        <dt className="text-muted-foreground">Employees</dt>
        <dd>{assignedNames.join(', ') || 'None assigned'}</dd>
        {editors.length ? (
          <>
            <dt className="text-muted-foreground">Editing now</dt>
            <dd>{editors.join(', ')}</dd>
          </>
        ) : null}
      </dl>
    </Modal>
  );
}
