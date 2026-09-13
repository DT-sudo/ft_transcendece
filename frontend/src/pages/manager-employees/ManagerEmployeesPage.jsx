import { useState } from 'react';

import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { initialsFromName } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Plus } from '../../components/Icons.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { CredentialsModal, EmployeeFormModal, PositionsModal } from './EmployeeModals.jsx';

function EmployeeRow({ employee, showRole, onEdit, onResetPassword, onDelete }) {
  return (
    <tr>
      <td>
        <div className="avatar">{initialsFromName(employee.fullName)}</div>
      </td>
      <td className="text-sm">{employee.employeeId}</td>
      <td className="font-medium">{employee.fullName}</td>
      {showRole ? (
        <td>
          <span className="badge badge-outline">{employee.roleLabel}</span>
        </td>
      ) : null}
      <td>{employee.position ? <span className="badge badge-default">{employee.position}</span> : null}</td>
      <td className="text-sm">{employee.email}</td>
      <td className="text-end whitespace-nowrap">
        <button className="btn btn-ghost btn-sm" type="button" onClick={() => onEdit(employee)}>
          Edit
        </button>
        <button className="btn btn-ghost btn-sm" type="button" onClick={() => onResetPassword(employee)}>
          Reset password
        </button>
        <button className="btn btn-ghost btn-sm btn-icon-destructive" type="button" onClick={() => onDelete(employee)}>
          Delete
        </button>
      </td>
    </tr>
  );
}

/** The Team page. Admins get every other account plus a role column and picker (`roles`); managers get employees. */
export function ManagerEmployeesPage() {
  const { data } = getBootstrap();
  const { employees, roles, positions, credentials, urls } = data;
  const noun = roles ? 'user' : 'employee';

  const [employeeForm, setEmployeeForm] = useState(null);
  const [showPositions, setShowPositions] = useState(false);
  const [showCredentials, setShowCredentials] = useState(Boolean(credentials));
  const [pendingReset, setPendingReset] = useState(null);
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
              Add {noun}
            </button>
            <button className="btn btn-outline" type="button" onClick={() => setShowPositions(true)}>
              Manage positions
            </button>
          </div>
        </div>

        <div className="card mt-3">
          <table className="table" aria-label={roles ? 'User list' : 'Employee list'}>
            <thead>
              <tr>
                <th>Avatar</th>
                <th>Employee ID</th>
                <th>Full name</th>
                {roles ? <th>Role</th> : null}
                <th>Position</th>
                <th>Email</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.length === 0 ? (
                <tr>
                  <td colSpan={roles ? 7 : 6} className="p-8 text-center text-sm text-muted-foreground">
                    No employees yet. Add your first employee to start assigning shifts.
                  </td>
                </tr>
              ) : (
                employees.map((employee) => (
                  <EmployeeRow
                    key={employee.id}
                    employee={employee}
                    showRole={Boolean(roles)}
                    onEdit={(target) => setEmployeeForm({ employee: target, action: urlFromTemplate(urls.update, target.id) })}
                    onResetPassword={setPendingReset}
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
          title="Reset password"
          message="Are you sure you want to reset the password for:"
          detail={`${pendingReset.employeeId} (${pendingReset.email})`}
          onCancel={() => setPendingReset(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.resetPassword, pendingReset.id))}
        />
      ) : null}

      {pendingDelete ? (
        <ConfirmModal
          title={`Delete ${noun}`}
          message={`Are you sure you want to delete this ${noun}?`}
          detail={`${pendingDelete.employeeId} (${pendingDelete.email})`}
          footnote={`This will remove the ${noun} and their assignments.`}
          confirmText="Yes, delete"
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.delete, pendingDelete.id))}
        />
      ) : null}
    </AppShell>
  );
}
