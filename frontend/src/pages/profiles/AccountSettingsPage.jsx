import { useEffect, useState } from 'react';

import { getBootstrap, submitPost } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Avatar } from '../../components/Avatar.jsx';
import { CsrfInput, Field } from '../../components/Field.jsx';
import { Settings, Trash, UserIcon } from '../../components/Icons.jsx';

/** Names the card a native form belongs to; the server re-renders that card's errors in place. */
const Section = ({ name }) => <input type="hidden" name="section" value={name} />;

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
    setProblem(tooBig ? `The picture must be ${maxMegabytes} MB or smaller.` : '');
    setPreview(file && !tooBig ? URL.createObjectURL(file) : null);
    if (tooBig) event.target.value = '';
  };
  const message = problem || error;

  return (
    <section className="card p-4" aria-labelledby="avatarTitle">
      <h2 id="avatarTitle" className="card-title">
        Profile picture
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        JPEG, PNG, WebP or GIF, up to {maxMegabytes} MB. It is cropped to a square; without one, your initials are
        shown.
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <Avatar name={person.fullName} src={preview || person.avatarUrl} size="lg" primary />
        <form className="flex flex-wrap items-center gap-2" method="post" action={action} encType="multipart/form-data">
          <CsrfInput />
          <Section name="avatar" />
          <label className="sr-only" htmlFor="avatarFile">
            New profile picture
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
          <button className="btn btn-primary" type="submit" disabled={!preview}>
            Upload
          </button>
        </form>
        {person.avatarUrl ? (
          <button
            className="btn btn-ghost btn-icon-destructive"
            type="button"
            onClick={() => submitPost(action, { section: 'remove_avatar' })}
          >
            <Trash size={16} />
            Remove picture
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
        Profile
      </h2>
      <form className="mt-4" method="post" action={action}>
        <CsrfInput />
        <Section name="profile" />
        <Field
          id="fullName"
          name="full_name"
          label="Full name"
          autoComplete="name"
          required
          minLength={2}
          maxLength={150}
          defaultValue={values.fullName}
          error={errors.full_name}
        />
        <Field
          id="email"
          name="email"
          type="email"
          label="Email"
          autoComplete="email"
          hint="You sign in with this address."
          required
          defaultValue={values.email}
          error={errors.email}
        />
        <Field
          as="textarea"
          id="bio"
          name="bio"
          label="Bio"
          rows={3}
          maxLength={300}
          hint="Up to 300 characters, shown on your profile."
          defaultValue={values.bio}
          error={errors.bio}
        />
        <Field
          id="currentPassword"
          name="current_password"
          type="password"
          label="Current password"
          autoComplete="current-password"
          hint="Only needed to change your email."
          error={errors.current_password}
        />
        <button className="btn btn-primary" type="submit">
          Save profile
        </button>
      </form>
    </section>
  );
}

function PasswordCard({ errors, action }) {
  return (
    <section className="card p-4" aria-labelledby="passwordTitle">
      <h2 id="passwordTitle" className="card-title">
        Password
      </h2>
      <form className="mt-4" method="post" action={action}>
        <CsrfInput />
        <Section name="password" />
        <Field
          id="oldPassword"
          name="old_password"
          type="password"
          label="Current password"
          autoComplete="current-password"
          required
          error={errors.old_password}
        />
        <Field
          id="newPassword1"
          name="new_password1"
          type="password"
          label="New password"
          autoComplete="new-password"
          hint="Minimum 8 characters, not entirely numeric, and not similar to your name or email."
          required
          minLength={8}
          error={errors.new_password1}
        />
        <Field
          id="newPassword2"
          name="new_password2"
          type="password"
          label="Confirm new password"
          autoComplete="new-password"
          required
          minLength={8}
          error={errors.new_password2}
        />
        <button className="btn btn-primary" type="submit">
          Change password
        </button>
      </form>
    </section>
  );
}

/** Your own profile, picture and password; each card is a native form that posts to this page. */
export function AccountSettingsPage() {
  const { urls, data } = getBootstrap();
  const { values, errors, person, avatar } = data;

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="card page-toolbar-card">
          <div className="flex flex-wrap items-center gap-3">
            <Settings size={20} className="text-muted-foreground" />
            <div className="flex-1">
              <h1 className="card-title">Account settings</h1>
              <p className="text-sm text-muted-foreground">Your profile, picture and password.</p>
            </div>
            <a className="btn btn-outline" href={person.profileUrl}>
              <UserIcon size={16} />
              View my profile
            </a>
          </div>
        </div>

        <div className="mx-auto mt-3 flex max-w-3xl flex-col gap-3">
          <AvatarCard person={person} limits={avatar} error={errors.avatar} action={urls.settings} />
          <ProfileCard values={values} errors={errors.profile} action={urls.settings} />
          <PasswordCard errors={errors.password} action={urls.settings} />
          <p className="text-sm text-muted-foreground">
            To download or delete your data, see{' '}
            <a className="footer-link" href={urls.privacyCenter}>
              Privacy & my data
            </a>
            .
          </p>
        </div>
      </main>
    </AppShell>
  );
}
