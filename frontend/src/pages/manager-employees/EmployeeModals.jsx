import { useState } from 'react';

import { submitPost, urlFromTemplate } from '../../app/http.js';
import { CsrfInput, Field, SelectField } from '../../components/Field.jsx';
import { Trash } from '../../components/Icons.jsx';
import { ConfirmModal, Modal } from '../../components/Modal.jsx';

/**
 * Create or edit an account, given a row from the Team payload (an empty object when creating).
 * Admins also pick the role (`roles`); only employees have a position.
 * Native form: the browser checks required/type, Django validates.
 */
export function EmployeeFormModal({ employee, action, roles, positions, onClose }) {
  const isEdit = Boolean(employee.id);
  const noun = roles ? 'User' : 'Employee';
  const [role, setRole] = useState(employee.role ?? 'employee');

  return (
    <Modal
      title={isEdit ? `Edit ${noun}` : `Add New ${noun}`}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-outline" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" type="submit" form="employeeForm">
            {isEdit ? 'Save' : `Create ${noun.toLowerCase()}`}
          </button>
        </>
      }
    >
      <form id="employeeForm" className="modal-body" method="post" action={action}>
        <CsrfInput />

        <Field id="employeeFullName" name="full_name" label="Full name" placeholder="Enter full name" required defaultValue={employee.fullName} />
        <Field id="employeeEmail" name="email" type="email" label="Email / Login" placeholder="Enter email" required defaultValue={employee.email} />
        {roles ? (
          <SelectField
            id="employeeRole"
            name="role"
            label="Role"
            placeholder="Select role..."
            required
            options={roles}
            value={role}
            onChange={(event) => setRole(event.target.value)}
          />
        ) : null}
        {role === 'employee' ? (
          <SelectField
            id="employeePosition"
            name="position"
            label="Position"
            placeholder="Select position..."
            required
            options={positions}
            defaultValue={employee.positionId ?? ''}
          />
        ) : null}

        {isEdit ? null : (
          <p className="text-sm text-muted-foreground">
            A password is generated automatically and shown <strong>only once</strong> after creation.
          </p>
        )}
      </form>
    </Modal>
  );
}

/** The generated password, shown once after creating an employee or resetting their password. */
export function CredentialsModal({ credentials, onClose }) {
  return (
    <Modal
      title="Credentials (shown once)"
      onClose={onClose}
      footer={
        <button className="btn btn-primary" type="button" onClick={onClose}>
          Done
        </button>
      }
    >
      <div className="modal-body">
        <p className="text-sm text-muted-foreground">Login</p>
        <p className="font-medium break-all">{credentials.login}</p>
        <p className="mt-3 text-sm text-muted-foreground">Password</p>
        <p className="font-medium break-all">{credentials.password}</p>
        <p className="mt-4 text-sm text-muted-foreground">This password is shown only once. Copy and share it securely.</p>
      </div>
    </Modal>
  );
}

export function PositionsModal({ positions, urls, onClose }) {
  const [pendingDelete, setPendingDelete] = useState(null);

  return (
    <>
      <Modal
        title="Manage positions"
        onClose={onClose}
        maxWidth="720px"
        footer={
          <button className="btn btn-outline" type="button" onClick={onClose}>
            Done
          </button>
        }
      >
        <div className="modal-body">
          <form className="flex gap-2" method="post" action={urls.positionCreate}>
            <CsrfInput />
            <input className="form-input" name="name" placeholder="New position name (e.g., Barista)" maxLength={25} required />
            <button className="btn btn-primary btn-sm" type="submit">
              Add position
            </button>
          </form>

          <table className="table mt-4" aria-label="Position list">
            <thead>
              <tr>
                <th>Position</th>
                <th className="w-45">Actions</th>
              </tr>
            </thead>
            <tbody>
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={2} className="text-sm text-muted-foreground">
                    No positions yet.
                  </td>
                </tr>
              ) : (
                positions.map((position) => (
                  <tr key={position.id}>
                    <td>{position.name}</td>
                    <td className="text-end">
                      <button
                        className="btn btn-ghost btn-icon btn-icon-destructive"
                        type="button"
                        aria-label={`Delete position ${position.name}`}
                        title="Delete"
                        onClick={() => setPendingDelete(position)}
                      >
                        <Trash />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Modal>

      {pendingDelete ? (
        <ConfirmModal
          title="Delete position"
          message="Delete this position?"
          detail={pendingDelete.name}
          footnote="A position still required by a shift cannot be deleted."
          confirmText="Yes, delete"
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => submitPost(urlFromTemplate(urls.positionDelete, pendingDelete.id))}
        />
      ) : null}
    </>
  );
}
