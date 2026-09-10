import { useState } from 'react';

import { getBootstrap, submitPost, urlFromTemplate } from '../../app/http.js';
import { initialsFromName } from '../../app/shifts.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Dropdown } from '../../components/Menus.jsx';
import { MoreVertical, Plus } from '../../components/Icons.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { CredentialsModal, EmployeeFormModal, PositionsModal } from './EmployeeModals.jsx';

function EmployeeRow({ employee, onEdit, onResetPassword, onDelete }) {
  return (
    <tr>
      <td>
        <div className="avatar">{initialsFromName(employee.fullName)}</div>
      </td>
      <td className="text-sm">{employee.employeeId}</td>
      <td className="font-medium">{employee.fullName}</td>
      <td>
        {employee.position ? (
          <span className="badge badge-default">{employee.position}</span>
        ) : (
          <span className="text-sm text-muted-foreground">—</span>
        )}
      </td>
      <td className="text-sm">{employee.email}</td>
      <td className="table-actions-cell">
        <Dropdown
          fixed
          trigger={({ toggle }) => (
            <button className="btn btn-ghost btn-icon" type="button" onClick={toggle} aria-label="Row actions">
              <MoreVertical />
            </button>
          )}
        >
          {({ close }) => (
            <>
              <button
                className="dropdown-item"
                type="button"
                onClick={() => {
                  close();
                  onEdit(employee);
                }}
              >
                View/Edit
              </button>
              <button
                className="dropdown-item"
                type="button"
                onClick={() => {
                  close();
                  onResetPassword(employee);
                }}
              >
                Reset password
              </button>
              <div className="dropdown-divider" />
              <button
                className="dropdown-item dropdown-item-destructive"
                type="button"
                onClick={() => {
                  close();
                  onDelete(employee);
                }}
              >
                Delete
              </button>
            </>
          )}
        </Dropdown>
      </td>
    </tr>
  );
}

export function ManagerEmployeesPage() {
  const { data } = getBootstrap();
  const { employees, positions, credentials, urls } = data;

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
              onClick={() =>
                setEmployeeForm({ mode: 'create', action: urls.create, initial: undefined })
              }
            >
              <Plus size={16} />
              Add employee
            </button>
            <button className="btn btn-outline" type="button" onClick={() => setShowPositions(true)}>
              Manage positions
            </button>
          </div>
        </div>

        <div className="card mt-3">
          <div className="max-h-[calc(100vh-220px)] overflow-auto">
            <table className="table table-fixed table-sticky-header" aria-label="Employee list">
              <colgroup>
                <col className="w-18" />
                <col className="w-32" />
                <col className="w-55" />
                <col className="w-40" />
                <col className="w-60" />
                <col className="w-20" />
              </colgroup>
              <thead>
                <tr>
                  <th>Avatar</th>
                  <th>Employee ID</th>
                  <th>Full name</th>
                  <th>Position</th>
                  <th>Email</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {employees.length === 0 ? (
                  <tr>
                    <td colSpan={6}>
                      <div className="flex flex-col items-center justify-center p-8 text-center">
                        <div className="text-lg font-medium">No employees yet</div>
                        <div className="mt-1 mb-4 text-sm text-muted-foreground">
                          Add your first employee to start assigning shifts.
                        </div>
                        <button
                          className="btn btn-primary"
                          type="button"
                          onClick={() => setEmployeeForm({ mode: 'create', action: urls.create })}
                        >
                          + Add employee
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  employees.map((employee) => (
                    <EmployeeRow
                      key={employee.id}
                      employee={employee}
                      onEdit={(target) =>
                        setEmployeeForm({
                          mode: 'edit',
                          action: urlFromTemplate(urls.update, target.id),
                          initial: {
                            fullName: target.fullName,
                            email: target.email,
                            positionId: target.positionId ? String(target.positionId) : '',
                          },
                        })
                      }
                      onResetPassword={setPendingReset}
                      onDelete={setPendingDelete}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {employeeForm ? (
        <EmployeeFormModal
          mode={employeeForm.mode}
          action={employeeForm.action}
          initial={employeeForm.initial}
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
          title="Delete employee"
          message="Are you sure you want to delete this employee?"
          detail={`${pendingDelete.employeeId} (${pendingDelete.email})`}
          footnote="This will remove the employee and their assignments."
          confirmText="Yes, delete"
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.delete, pendingDelete.id))}
        />
      ) : null}
    </AppShell>
  );
}
