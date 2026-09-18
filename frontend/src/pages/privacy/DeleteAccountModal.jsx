import { PrivacyPolicyLink } from '../../components/AppShell.jsx';
import { EmailField, Field, PostForm } from '../../components/Field.jsx';
import { FormFooter, Modal } from '../../components/Modal.jsx';
import { t, tx } from '../../i18n/index.js';

/**
 * Deletion is irreversible and cascades everything the Privacy Policy says
 * we hold about the account, so it asks for two things a session-hijacker
 * wouldn't have: the account's own email, typed out, and its password.
 */
export function DeleteAccountModal({ email, action, onClose }) {
  return (
    <Modal
      title={t('privacy.deleteTitle')}
      onClose={onClose}
      footer={<FormFooter form="deleteAccountForm" submitLabel={t('privacy.modalConfirm')} onCancel={onClose} destructive />}
    >
      <PostForm id="deleteAccountForm" className="modal-body" action={action}>

        <p className="text-sm">
          {tx('privacy.modalText', { policy: <PrivacyPolicyLink /> })}
        </p>

        <EmailField id="deleteConfirmEmail" name="confirm_email" label={t('privacy.typeEmail', { email })} placeholder={email} autoComplete="off" />
        <Field
          id="deleteConfirmPassword"
          name="confirm_password"
          type="password"
          label={t('privacy.confirmPassword')}
          autoComplete="current-password"
          required
        />
      </PostForm>
    </Modal>
  );
}
