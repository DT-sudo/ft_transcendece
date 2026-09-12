import { formatDateDMY, formatDurationMinutes, shiftDurationMinutes } from '../../app/dates.js';
import { CalendarIcon } from '../../components/Icons.jsx';
import { Modal } from '../../components/Modal.jsx';

/**
 * Search results open a read-only details view rather than the calendar's
 * edit/delete/publish modal: editing still happens on the Calendar page (via
 * its existing, untouched flow), which is what "Open in Calendar" jumps to.
 * Search and Analytics stay separate areas that only *read* shift data.
 */
export function SearchResultModal({ shift, calendarUrl, onClose }) {
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
        <a className="btn btn-primary" href={`${calendarUrl}?view=week&date=${shift.date}`}>
          Open in Calendar
        </a>
      }
    >
      <div className="modal-body">
        <div className="flex items-center gap-3">
          <CalendarIcon className="text-muted-foreground" />
          <div>
            <div className="font-medium">{formatDateDMY(shift.date)}</div>
            <div className="text-sm text-muted-foreground">
              {shift.start_time}-{shift.end_time}
            </div>
            <div className="text-sm text-muted-foreground">
              Duration: {formatDurationMinutes(shiftDurationMinutes(shift))}
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <span className="badge badge-default">{shift.position}</span>
          <span className="text-sm text-muted-foreground">
            Capacity: {shift.assigned_count}/{shift.capacity} filled
          </span>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">Manager: {shift.manager_name}</div>

        <div className="mt-4">
          <p className="mb-2 font-medium">Assigned Workers:</p>
          <div className="flex flex-col gap-1">
            {shift.worker_names.length === 0 ? (
              <div className="text-sm text-muted-foreground">No workers assigned.</div>
            ) : (
              shift.worker_names.map((name) => (
                <div className="text-sm" key={name}>
                  {name}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
