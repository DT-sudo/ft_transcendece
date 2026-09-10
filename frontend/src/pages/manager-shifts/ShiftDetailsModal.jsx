import { formatDuration, formatDate, shiftDurationMinutes } from '../../app/dates.js';
import { initialsFromName } from '../../app/shifts.js';
import { CalendarIcon } from '../../components/Icons.jsx';
import { Modal } from '../../components/Modal.jsx';

export function ShiftDetailsModal({ shift, assignedEmployees, onClose, onEdit, onDelete, onPublish }) {
  const isDraft = shift.status === 'draft';

  return (
    <Modal
      title="Shift Details"
      onClose={onClose}
      titleExtra={
        <span className={`badge ${isDraft ? 'badge-outline' : 'badge-success'}`}>
          {isDraft ? 'Draft' : 'Published'}
        </span>
      }
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
      <div className="modal-body">
        <div className="flex items-center gap-3">
          <CalendarIcon className="text-muted-foreground" />
          <div>
            <div className="font-medium">{formatDate(shift.date)}</div>
            <div className="text-sm text-muted-foreground">
              {shift.start_time}-{shift.end_time}
            </div>
            <div className="text-sm text-muted-foreground">
              Duration: {formatDuration(shiftDurationMinutes(shift))}
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <span className="badge badge-default">{shift.position}</span>
          <span className="text-sm text-muted-foreground">
            Capacity: {shift.assigned_count}/{shift.capacity} filled
          </span>
        </div>

        <div className="mt-4">
          <p className="mb-2 font-medium">Assigned Employees:</p>
          <div className="flex flex-col gap-2">
            {assignedEmployees.length === 0 ? (
              <div className="text-sm text-muted-foreground">No employees assigned.</div>
            ) : (
              assignedEmployees.map((employee) => (
                <div className="flex items-center gap-2" key={employee.id}>
                  <div className="avatar avatar-primary size-6 text-[0.625rem]">
                    {initialsFromName(employee.name)}
                  </div>
                  <span className="text-sm">{employee.name}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
