import { useState } from 'react';

import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Avatar } from '../../components/Avatar.jsx';
import { Plus } from '../../components/Icons.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { t } from '../../i18n/index.js';
import { CredentialsModal, EmployeeFormModal, PositionsModal } from './EmployeeModals.jsx';

/** "EMP-123456 (maya@example.com)": names the account in a confirmation. */
const accountLabel = (employee) => `${employee.employeeId} (${employee.email})`;

function EmployeeRow({ employee, showRole, onEdit, onResetPassword, onResetTwoFactor, onDelete }) {
  return (
    <tr>
      <td>
        <Avatar name={employee.fullName} src={employee.avatarUrl} />
      </td>
      <td className="text-sm">{employee.employeeId}</td>
      <td>
        <a className="person-name" href={employee.profileUrl}>
          {employee.fullName}
        </a>
        {employee.twoFactor ? (
          <span className="badge badge-success ms-2" title={t('team.twoFactorOn')}>
            2FA
          </span>
        ) : null}
      </td>
      {showRole ? (
        <td>
          <span className="badge badge-outline">{employee.roleLabel}</span>
        </td>
      ) : null}
      <td>{employee.position ? <span className="badge badge-default">{employee.position}</span> : null}</td>
      <td className="text-sm" dir="ltr">
        {employee.email}
      </td>
      <td className="text-end whitespace-nowrap">
        <button className="btn btn-ghost btn-sm" type="button" onClick={() => onEdit(employee)}>
          {t('common.edit')}
        </button>
        <button className="btn btn-ghost btn-sm" type="button" onClick={() => onResetPassword(employee)}>
          {t('team.resetPassword')}
        </button>
        {employee.twoFactor ? (
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => onResetTwoFactor(employee)}>
            {t('team.resetTwoFactor')}
          </button>
        ) : null}
        <button className="btn btn-ghost btn-sm btn-icon-destructive" type="button" onClick={() => onDelete(employee)}>
          {t('common.delete')}
        </button>
      </td>
    </tr>
  );
}

/** The Team page. Admins get every other account plus a role column and picker (`roles`); managers get employees. */
export function ManagerEmployeesPage() {
  const { data } = getBootstrap();
  const { employees, roles, positions, credentials, urls } = data;
  const isUsers = Boolean(roles);

  const [employeeForm, setEmployeeForm] = useState(null);
  const [showPositions, setShowPositions] = useState(false);
  const [showCredentials, setShowCredentials] = useState(Boolean(credentials));
  const [pendingReset, setPendingReset] = useState(null);
  const [pendingTwoFactorReset, setPendingTwoFactorReset] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="card page-toolbar-card">
          <div className="flex flex-wrap items-center gap-4">
            <button
              className="btn btn-primary"
              type="button"
              onClick={() => setEmployeeForm({ employee: {}, action: urls.create })}
            >
              <Plus size={16} />
              {isUsers ? t('team.addUser') : t('team.addEmployee')}
            </button>
            <button className="btn btn-outline" type="button" onClick={() => setShowPositions(true)}>
              {t('team.managePositions')}
            </button>
          </div>
        </div>

        <div className="card mt-3">
          <table className="table" aria-label={isUsers ? t('team.userList') : t('team.employeeList')}>
            <thead>
              <tr>
                <th>{t('team.avatar')}</th>
                <th>{t('team.employeeId')}</th>
                <th>{t('team.fullName')}</th>
                {roles ? <th>{t('team.role')}</th> : null}
                <th>{t('team.position')}</th>
                <th>{t('team.email')}</th>
                <th>{t('team.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {employees.length === 0 ? (
                <tr>
                  <td colSpan={roles ? 7 : 6} className="p-8 text-center text-sm text-muted-foreground">
                    {t('team.empty')}
                  </td>
                </tr>
              ) : (
                employees.map((employee) => (
                  <EmployeeRow
                    key={employee.id}
                    employee={employee}
                    showRole={isUsers}
                    onEdit={(target) => setEmployeeForm({ employee: target, action: urlFromTemplate(urls.update, target.id) })}
                    onResetPassword={setPendingReset}
                    onResetTwoFactor={setPendingTwoFactorReset}
                    onDelete={setPendingDelete}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>

      {employeeForm ? (
        <EmployeeFormModal
          employee={employeeForm.employee}
          action={employeeForm.action}
          roles={roles}
          positions={positions}
          onClose={() => setEmployeeForm(null)}
        />
      ) : null}

      {showPositions ? (
        <PositionsModal positions={positions} urls={urls} onClose={() => setShowPositions(false)} />
      ) : null}

      {showCredentials && credentials ? (
        <CredentialsModal credentials={credentials} onClose={() => setShowCredentials(false)} />
      ) : null}

      {pendingReset ? (
        <ConfirmModal
          title={t('team.resetPassword')}
          message={t('team.resetPasswordMessage')}
          detail={accountLabel(pendingReset)}
          onCancel={() => setPendingReset(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.resetPassword, pendingReset.id))}
        />
      ) : null}

      {pendingTwoFactorReset ? (
        <ConfirmModal
          title={t('team.resetTwoFactorTitle')}
          message={t('team.resetTwoFactorMessage')}
          detail={accountLabel(pendingTwoFactorReset)}
          footnote={t('team.resetTwoFactorNote')}
          confirmText={t('team.yesReset')}
          destructive
          onCancel={() => setPendingTwoFactorReset(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.resetTwoFactor, pendingTwoFactorReset.id))}
        />
      ) : null}

      {pendingDelete ? (
        <ConfirmModal
          title={isUsers ? t('team.deleteUser') : t('team.deleteEmployee')}
          message={isUsers ? t('team.deleteUserMessage') : t('team.deleteEmployeeMessage')}
          detail={accountLabel(pendingDelete)}
          footnote={isUsers ? t('team.deleteUserNote') : t('team.deleteEmployeeNote')}
          confirmText={t('common.yesDelete')}
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.delete, pendingDelete.id))}
        />
      ) : null}
    </AppShell>
  );
}
