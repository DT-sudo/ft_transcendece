import { useRef, useState } from 'react';

import { urlFromTemplate } from '../../app/http.js';
import { Trash } from '../../components/Icons.jsx';
import { ConfirmModal, Modal } from '../../components/Modal.jsx';
import { CsrfInput, PostForm } from '../../components/PostForm.jsx';

function PositionSelect({ id, positions, value, onChange }) {
  return (
    <select
      className="form-select"
      id={id}
      name="position"
      required
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">Select position...</option>
      {positions.map((position) => (
        <option key={position.id} value={position.id}>
          {position.name}
        </option>
      ))}
    </select>
  );
}

const EMPTY_EMPLOYEE = { fullName: '', email: '', positionId: '' };

export function EmployeeFormModal({ mode, action, initial = EMPTY_EMPLOYEE, positions, onClose }) {
  const [form, setForm] = useState(initial);
  const isEdit = mode === 'edit';
  const formId = 'employeeForm';

  return (
    <Modal
      title={isEdit ? 'View/Edit Employee' : 'Add New Employee'}
      onClose={onClose}
      footer={
        <>
          {isEdit ? null : (
            <button className="btn btn-outline" type="button" onClick={onClose}>
              Cancel
            </button>
          )}
          <button className="btn btn-primary" type="submit" form={formId}>
            {isEdit ? 'Save' : 'Create employee'}
          </button>
        </>
      }
    >
      <form id={formId} className="modal-body" method="post" action={action}>
        <CsrfInput />

        <div className="mb-4">
          <label className="form-label" htmlFor="employeeFullName">
            Full name *
          </label>
          <input
            type="text"
            className="form-input"
            id="employeeFullName"
            name="full_name"
            placeholder="Enter full name"
            required
            value={form.fullName}
            onChange={(event) => setForm({ ...form, fullName: event.target.value })}
          />
        </div>

        <div className="mb-4">
          <label className="form-label" htmlFor="employeeEmail">
            Email / Login *
          </label>
          <input
            type="email"
            className="form-input"
            id="employeeEmail"
            name="email"
            placeholder="Enter email"
            required
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
          />
        </div>

        <div className="mb-4">
          <label className="form-label" htmlFor="employeePosition">
            Position *
          </label>
          <PositionSelect
            id="employeePosition"
            positions={positions}
            value={form.positionId}
            onChange={(positionId) => setForm({ ...form, positionId })}
          />
        </div>

        {isEdit ? null : (
          <p className="text-sm text-muted-foreground">
            A password is generated automatically and shown <strong>only once</strong> after creation.
          </p>
        )}
      </form>
    </Modal>
  );
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
  }
}

export function CredentialsModal({ credentials, onClose }) {
  const rows = [
    { label: 'Login', value: credentials.login },
    { label: 'Password', value: credentials.password },
  ];

  return (
    <Modal
      title="Credentials (shown once)"
      onClose={onClose}
      maxWidth="560px"
      footer={
        <button className="btn btn-primary" type="button" onClick={onClose}>
          Done
        </button>
      }
    >
      <div className="modal-body">
        <div className="rounded-card border border-dashed border-border bg-linear-to-b from-muted to-transparent p-3">
          {rows.map((row, index) => (
            <div key={row.label} className={index ? 'mt-3' : ''}>
              <div className="text-sm text-muted-foreground">{row.label}</div>
              <div className="mt-1 flex items-center justify-between gap-2">
                <div className="font-medium break-all">{row.value}</div>
                <button
                  className="btn btn-ghost btn-sm"
                  type="button"
                  onClick={() => copyText(row.value)}
                >
                  Copy
                </button>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-3 text-sm text-muted-foreground">
          This password is shown only once. Copy and share it securely.
        </p>
      </div>
    </Modal>
  );
}

export function PositionsModal({ positions, urls, onClose }) {
  const [pendingDelete, setPendingDelete] = useState(null);
  const deleteFormRef = useRef(null);

  const submitDelete = () => {
    deleteFormRef.current.action = urlFromTemplate(urls.positionDelete, pendingDelete.id);
    deleteFormRef.current.submit();
  };

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
          <div className="card p-3">
            <form className="flex gap-2" method="post" action={urls.positionCreate}>
              <CsrfInput />
              <input
                className="form-input"
                name="name"
                placeholder="New position name (e.g., Barista)"
                required
              />
              <input type="hidden" name="is_active" value="on" readOnly />
              <button className="btn btn-primary btn-sm" type="submit">
                Add position
              </button>
            </form>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="table" aria-label="Position list">
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
                      <td>
                        <div className="flex items-center justify-end">
                          <button
                            className="btn btn-ghost btn-icon btn-icon-destructive"
                            type="button"
                            aria-label={`Delete position ${position.name}`}
                            title="Delete"
                            onClick={() => setPendingDelete(position)}
                          >
                            <Trash />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Modal>

      <PostForm formRef={deleteFormRef} action={urls.positionDelete} />

      {pendingDelete ? (
        <ConfirmModal
          title="Delete position"
          message="Delete this position?"
          detail={pendingDelete.name}
          footnote="A position still required by a shift cannot be deleted."
          confirmText="Yes, delete"
          destructive
          onCancel={() => setPendingDelete(null)}
          onConfirm={submitDelete}
        />
      ) : null}
    </>
  );
}
