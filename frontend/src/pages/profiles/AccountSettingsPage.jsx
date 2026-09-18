import { useEffect, useState } from 'react';

import { formatDate } from '../../app/dates.js';
import { getBootstrap, submitPost } from '../../app/http.js';
import { AppShell, PageHeader } from '../../components/AppShell.jsx';
import { Avatar } from '../../components/Avatar.jsx';
import { EmailField, Field, FullNameField, PostForm } from '../../components/Field.jsx';
import { Settings, Trash, UserIcon } from '../../components/Icons.jsx';
import { Modal } from '../../components/Modal.jsx';
import { t, tx } from '../../i18n/index.js';

function AvatarCard({ person, limits, error, action }) {
  const [preview, setPreview] = useState(null);
  const [problem, setProblem] = useState('');
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );

  const maxMegabytes = limits.maxBytes / 2 ** 20;

  // The server checks everything again; this only spares uploading a file it would refuse for size.
  const pick = (event) => {
    const file = event.target.files[0];
    const tooBig = file && file.size > limits.maxBytes;
    setProblem(tooBig ? t('settings.avatarTooBig', { size: maxMegabytes }) : '');
    setPreview(file && !tooBig ? URL.createObjectURL(file) : null);
    if (tooBig) event.target.value = '';
  };
  const message = problem || error;

  return (
    <section className="card p-4" aria-labelledby="avatarTitle">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <Avatar name={person.fullName} src={preview || person.avatarUrl} size="md" primary />
        <div className="min-w-0 flex-1">
          <h2 id="avatarTitle" className="card-title">
            {t('settings.avatarTitle')}
          </h2>
          <p className="text-sm text-muted-foreground">{t('settings.avatarHint', { size: maxMegabytes })}</p>
        </div>
        <PostForm className="flex flex-wrap items-center gap-2" action={action} encType="multipart/form-data" fields={{ section: 'avatar' }}>
          <label className="sr-only" htmlFor="avatarFile">
            {t('settings.avatarFile')}
          </label>
          <input
            id="avatarFile"
            name="avatar"
            type="file"
            accept={limits.accept}
            className="form-input w-auto max-w-full"
            aria-invalid={message ? 'true' : undefined}
            aria-describedby={message ? 'avatarError' : undefined}
            required
            onChange={pick}
          />
          <button className="btn btn-primary btn-sm" type="submit" disabled={!preview}>
            {t('settings.upload')}
          </button>
        </PostForm>
        {person.avatarUrl ? (
          <button
            className="btn btn-ghost btn-sm btn-icon-destructive"
            type="button"
            onClick={() => submitPost(action, { section: 'remove_avatar' })}
          >
            <Trash size={16} />
            {t('settings.removePicture')}
          </button>
        ) : null}
      </div>
      {message ? (
        <p id="avatarError" className="form-error-text" role="alert">
          {message}
        </p>
      ) : null}
    </section>
  );
}

function ProfileCard({ values, errors, action }) {
  return (
    <section className="card p-4" aria-labelledby="profileTitle">
      <h2 id="profileTitle" className="card-title">
        {t('settings.profileTitle')}
      </h2>
      <PostForm className="mt-4" action={action} fields={{ section: 'profile' }}>
        <FullNameField id="fullName" defaultValue={values.fullName} error={errors.full_name} />
        <EmailField id="email" hint={t('settings.emailHint')} defaultValue={values.email} error={errors.email} />
        <Field
          as="textarea"
          id="bio"
          name="bio"
          label={t('settings.bio')}
          rows={3}
          maxLength={300}
          hint={t('settings.bioHint')}
          defaultValue={values.bio}
          error={errors.bio}
        />
        <Field
          id="currentPassword"
          name="current_password"
          type="password"
          label={t('settings.currentPassword')}
          autoComplete="current-password"
          hint={t('settings.currentPasswordHint')}
          error={errors.current_password}
        />
        <button className="btn btn-primary" type="submit">
          {t('settings.saveProfile')}
        </button>
      </PostForm>
    </section>
  );
}

function PasswordCard({ errors, action }) {
  return (
    <section className="card p-4" aria-labelledby="passwordTitle">
      <h2 id="passwordTitle" className="card-title">
        {t('settings.passwordTitle')}
      </h2>
      <PostForm className="mt-4" action={action} fields={{ section: 'password' }}>
        <Field
          id="oldPassword"
          name="old_password"
          type="password"
          label={t('settings.currentPassword')}
          autoComplete="current-password"
          required
          error={errors.old_password}
        />
        <Field
          id="newPassword1"
          name="new_password1"
          type="password"
          label={t('settings.newPassword')}
          autoComplete="new-password"
          hint={t('signup.passwordHint')}
          required
          minLength={8}
          error={errors.new_password1}
        />
        <Field
          id="newPassword2"
          name="new_password2"
          type="password"
          label={t('settings.confirmNewPassword')}
          autoComplete="new-password"
          required
          minLength={8}
          error={errors.new_password2}
        />
        <button className="btn btn-primary" type="submit">
          {t('settings.changePassword')}
        </button>
      </PostForm>
    </section>
  );
}

/** "JBSWY3DPEHPK3PXP..." -> "JBSW Y3DP EHPK 3PXP ...", easier to type into an app by hand. */
const groupKey = (secret) => secret.match(/.{1,4}/g).join(' ');

function TwoFactorSetup({ setup, errors, action }) {
  return (
    <ol className="mt-4 flex flex-col gap-5 text-sm">
      <li>
        <p className="font-medium">{t('settings.scanStep')}</p>
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <img
            src={setup.qr}
            alt={t('settings.qrAlt')}
            className="size-45 rounded-md border border-border bg-white"
          />
          <div className="min-w-0 flex-1">
            <p className="text-muted-foreground">{t('settings.manualKey')}</p>
            <code dir="ltr" className="mt-1 block font-mono text-base break-all select-all">
              {groupKey(setup.secret)}
            </code>
          </div>
        </div>
      </li>
      <li>
        <p className="font-medium">{t('settings.codeStep')}</p>
        <PostForm className="mt-3" action={action} fields={{ section: '2fa_confirm' }}>
          <Field
            id="setupCode"
            name="code"
            dir="ltr"
            label={t('settings.codeFromApp')}
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            title={t('twoFactorLogin.sixDigits')}
            maxLength={6}
            required
            error={errors.code}
          />
          <div className="flex flex-wrap gap-2">
            <button className="btn btn-primary" type="submit">
              {t('settings.turnOn')}
            </button>
            <button className="btn btn-outline" type="button" onClick={() => submitPost(action, { section: '2fa_cancel' })}>
              {t('common.cancel')}
            </button>
          </div>
        </PostForm>
      </li>
    </ol>
  );
}

function TwoFactorManage({ state, action }) {
  const { enabledAt, recoveryCodesLeft, errors } = state;

  return (
    <>
      <p className="mt-1 text-sm text-muted-foreground">
        {t('settings.enabledSince', { date: formatDate(enabledAt.slice(0, 10)) })}
      </p>
      <p className={`mt-1 text-sm ${recoveryCodesLeft <= 2 ? 'text-destructive' : 'text-muted-foreground'}`}>
        {t('settings.codesLeft', { count: recoveryCodesLeft })}
      </p>
      {/* One form, two actions: each submit button posts its own `section`. */}
      <PostForm className="mt-4" action={action}>
        <p className="mb-3 text-sm">{t('settings.confirmItsYou')}</p>
        <Field
          id="twoFactorPassword"
          name="password"
          type="password"
          label={t('settings.currentPassword')}
          autoComplete="current-password"
          required
          error={errors.password}
        />
        <Field
          id="twoFactorCode"
          name="code"
          dir="ltr"
          label={t('settings.codeOrRecovery')}
          autoComplete="one-time-code"
          autoCapitalize="none"
          spellCheck={false}
          maxLength={32}
          required
          error={errors.code}
        />
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-outline" type="submit" name="section" value="2fa_recovery">
            {t('settings.newCodes')}
          </button>
          <button className="btn btn-destructive" type="submit" name="section" value="2fa_disable">
            {t('settings.turnOff')}
          </button>
        </div>
      </PostForm>
    </>
  );
}

function TwoFactorCard({ state, action }) {
  const { enabled, setup, errors } = state;

  let body;
  if (enabled) {
    body = <TwoFactorManage state={state} action={action} />;
  } else if (setup) {
    body = <TwoFactorSetup setup={setup} errors={errors} action={action} />;
  } else {
    body = (
      <>
        <p className="mt-1 text-sm text-muted-foreground">{t('settings.twoFactorIntro')}</p>
        <PostForm className="mt-4" action={action} fields={{ section: '2fa_start' }}>
          <button className="btn btn-primary" type="submit">
            {t('settings.setUpTwoFactor')}
          </button>
        </PostForm>
      </>
    );
  }

  return (
    <section id="security" className="card p-4" aria-labelledby="twoFactorTitle">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="twoFactorTitle" className="card-title">
          {t('settings.twoFactorTitle')}
        </h2>
        <span className={`badge ${enabled ? 'badge-success' : 'badge-outline'}`}>
          {enabled ? t('settings.on') : t('settings.off')}
        </span>
      </div>
      {body}
    </section>
  );
}

/** Shown once, right after the codes were created: the server keeps only their hashes. */
function RecoveryCodesModal({ codes, onClose }) {
  const [copied, setCopied] = useState(false);
  const text = codes.join('\n');

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const download = () => {
    const file = `${t('settings.codesFileHeading')}\n\n${text}\n`;
    const url = URL.createObjectURL(new Blob([file], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'planshift-recovery-codes.txt';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <Modal
      title={t('settings.codesTitle')}
      onClose={onClose}
      footer={
        <button className="btn btn-primary" type="button" onClick={onClose}>
          {t('settings.savedThem')}
        </button>
      }
    >
      <div className="modal-body">
        <p className="text-sm">{t('settings.codesText')}</p>
        <ul dir="ltr" className="mt-4 grid grid-cols-2 gap-2 font-mono text-sm" aria-label={t('settings.codesList')}>
          {codes.map((code) => (
            <li key={code} className="rounded-md border border-border px-2 py-1 text-center">
              {code}
            </li>
          ))}
        </ul>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button className="btn btn-outline btn-sm" type="button" onClick={copy}>
            {t('settings.copy')}
          </button>
          <button className="btn btn-outline btn-sm" type="button" onClick={download}>
            {t('settings.download')}
          </button>
          <span className="text-sm text-muted-foreground" role="status">
            {copied ? t('settings.copied') : ''}
          </span>
        </div>
      </div>
    </Modal>
  );
}

/** Your own profile, picture, password and two-factor authentication; each card is a native form that posts to this page,
 * naming itself in `section` so the server re-renders that card's errors in place.
 *
 * The language is not here: the footer switcher on every page is the one place to change it. */
export function AccountSettingsPage() {
  const { urls, data } = getBootstrap();
  const { values, errors, person, avatar, twoFactor } = data;
  const [recoveryCodes, setRecoveryCodes] = useState(twoFactor.recoveryCodes);

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <PageHeader icon={Settings} title={t('settings.title')}>
          <a className="btn btn-outline" href={person.profileUrl}>
            <UserIcon size={16} />
            {t('settings.viewProfile')}
          </a>
        </PageHeader>

        <div className="mx-auto mt-3 flex max-w-3xl flex-col gap-3">
          <AvatarCard person={person} limits={avatar} error={errors.avatar} action={urls.settings} />
          <ProfileCard values={values} errors={errors.profile} action={urls.settings} />
          <PasswordCard errors={errors.password} action={urls.settings} />
          <TwoFactorCard state={twoFactor} action={urls.settings} />
          <p className="text-sm text-muted-foreground">
            {tx('settings.privacyLink', {
              link: (
                <a className="footer-link" href={urls.privacyCenter}>
                  {t('header.privacy')}
                </a>
              ),
            })}
          </p>
        </div>
      </main>

      {recoveryCodes ? <RecoveryCodesModal codes={recoveryCodes} onClose={() => setRecoveryCodes(null)} /> : null}
    </AppShell>
  );
}
