import { formatDate, formatDuration, shiftDurationMinutes } from '../../app/dates.js';
import { Modal } from '../../components/Modal.jsx';
import { ShiftStatusBadge } from '../../components/ShiftStatusBadge.jsx';
import { t } from '../../i18n/index.js';

export function ShiftDetailsModal({ shift, assignedNames, editors, onClose, onEdit, onDelete, onPublish }) {
  const isDraft = shift.status === 'draft';

  return (
    <Modal
      title={t('shifts.detailsTitle')}
      onClose={onClose}
      titleExtra={<ShiftStatusBadge status={shift.status} />}
      footer={
        <>
          <button className="btn btn-destructive" type="button" onClick={onDelete}>
            {t('common.delete')}
          </button>
          {isDraft ? (
            <button className="btn btn-primary" type="button" onClick={onPublish}>
              {t('shifts.publish')}
            </button>
          ) : null}
          <button className="btn btn-outline" type="button" onClick={onEdit}>
            {t('common.edit')}
          </button>
        </>
      }
    >
      <dl className="modal-body grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
        <dt className="text-muted-foreground">{t('shifts.date')}</dt>
        <dd>{formatDate(shift.date)}</dd>
        <dt className="text-muted-foreground">{t('shifts.time')}</dt>
        <dd>
          {shift.start_time}-{shift.end_time} ({formatDuration(shiftDurationMinutes(shift))})
        </dd>
        <dt className="text-muted-foreground">{t('shifts.position')}</dt>
        <dd>{shift.position}</dd>
        <dt className="text-muted-foreground">{t('shifts.staffed')}</dt>
        <dd>
          {shift.assigned_employee_ids.length}/{shift.capacity}
        </dd>
        <dt className="text-muted-foreground">{t('shifts.employees')}</dt>
        <dd>{assignedNames.join(', ') || t('shifts.noneAssigned')}</dd>
        {editors.length ? (
          <>
            <dt className="text-muted-foreground">{t('shifts.editingNow')}</dt>
            <dd>{editors.join(', ')}</dd>
          </>
        ) : null}
      </dl>
    </Modal>
  );
}
