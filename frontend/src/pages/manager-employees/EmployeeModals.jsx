import { useState } from 'react';

import { urlFromTemplate } from '../../app/http.js';
import { EmailField, FullNameField, PostForm, SelectField } from '../../components/Field.jsx';
import { Trash } from '../../components/Icons.jsx';
import { DeleteConfirmModal, FormFooter, Modal } from '../../components/Modal.jsx';
import { t, tx } from '../../i18n/index.js';

/**
 * Create or edit an account, given a row from the Users payload (an empty object when creating).
 * Only employees have a position, and giving one the "Manager" position promotes them.
 * Native form: the browser checks required/type, Django validates.
 */
export function EmployeeFormModal({ employee, action, roles, positions, onClose }) {
  const isEdit = Boolean(employee.id);
  const [role, setRole] = useState(employee.role ?? 'employee');

  return (
    <Modal
      title={isEdit ? t('team.editUser') : t('team.newUser')}
      onClose={onClose}
      footer={<FormFooter form="employeeForm" submitLabel={isEdit ? t('common.save') : t('team.createUser')} onCancel={onClose} />}
    >
      <PostForm id="employeeForm" className="modal-body" action={action}>

        {/* Someone else's details: the browser must not offer the admin's own. */}
        <FullNameField id="employeeFullName" label={t('team.fullName')} placeholder={t('team.fullNamePlaceholder')} autoComplete="off" defaultValue={employee.fullName} />
        <EmailField id="employeeEmail" label={t('team.emailLogin')} placeholder={t('team.emailPlaceholder')} autoComplete="off" defaultValue={employee.email} />
        <SelectField
          id="employeeRole"
          name="role"
          label={t('team.role')}
          placeholder={t('team.selectRole')}
          required
          options={roles}
          value={role}
          onChange={(event) => setRole(event.target.value)}
        />
        {role === 'employee' ? (
          <SelectField
            id="employeePosition"
            name="position"
            label={t('team.position')}
            placeholder={t('shifts.selectPosition')}
            required
            options={positions}
            defaultValue={employee.positionId ?? ''}
          />
        ) : null}

        {isEdit ? null : (
          <p className="text-sm text-muted-foreground">
            {tx('team.passwordNote', { once: <strong>{t('team.onlyOnce')}</strong> })}
          </p>
        )}
      </PostForm>
    </Modal>
  );
}

/** The generated password, shown once after creating an employee or resetting their password. */
export function CredentialsModal({ credentials, onClose }) {
  return (
    <Modal
      title={t('team.credentialsTitle')}
      onClose={onClose}
      footer={
        <button className="btn btn-primary" type="button" onClick={onClose}>
          {t('common.done')}
        </button>
      }
    >
      <div className="modal-body">
        <p className="text-sm text-muted-foreground">{t('team.login')}</p>
        <p dir="ltr" className="font-medium break-all">
          {credentials.login}
        </p>
        <p className="mt-3 text-sm text-muted-foreground">{t('team.password')}</p>
        <p dir="ltr" className="font-medium break-all">
          {credentials.password}
        </p>
        <p className="mt-4 text-sm text-muted-foreground">{t('team.credentialsNote')}</p>
      </div>
    </Modal>
  );
}

export function PositionsModal({ positions, urls, onClose }) {
  const [pendingDelete, setPendingDelete] = useState(null);

  return (
    <>
      <Modal
        title={t('team.positionsTitle')}
        onClose={onClose}
        maxWidth="720px"
        footer={
          <button className="btn btn-outline" type="button" onClick={onClose}>
            {t('common.done')}
          </button>
        }
      >
        <div className="modal-body">
          <PostForm className="flex gap-2" action={urls.positionCreate}>
            <input className="form-input" name="name" placeholder={t('team.newPosition')} aria-label={t('team.newPosition')} maxLength={25} required />
            <button className="btn btn-primary btn-sm" type="submit">
              {t('team.addPosition')}
            </button>
          </PostForm>

          <table className="table mt-4" aria-label={t('team.positionList')}>
            <thead>
              <tr>
                <th>{t('team.position')}</th>
                <th className="w-45 cell-actions">{t('team.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={2} className="text-sm text-muted-foreground">
                    {t('team.noPositions')}
                  </td>
                </tr>
              ) : (
                positions.map((position) => (
                  <tr key={position.id}>
                    <td>{position.name}</td>
                    <td className="cell-actions">
                      {position.name === 'Manager' ? (
                        // Offset by the ghost-button padding the cell trims, so the text starts under "Actions".
                        <span className="ms-3 text-xs text-muted-foreground">{t('team.permanentPosition')}</span>
                      ) : (
                        <button
                          className="btn btn-ghost btn-icon btn-icon-destructive ms-1"
                          type="button"
                          aria-label={t('team.deletePositionLabel', { name: position.name })}
                          title={t('common.delete')}
                          onClick={() => setPendingDelete(position)}
                        >
                          <Trash />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Modal>

      {pendingDelete ? (
        <DeleteConfirmModal
          title={t('team.deletePosition')}
          message={t('team.deletePositionMessage')}
          detail={pendingDelete.name}
          footnote={t('team.deletePositionNote')}
          action={urlFromTemplate(urls.positionDelete, pendingDelete.id)}
          onCancel={() => setPendingDelete(null)}
        />
      ) : null}
    </>
  );
}
