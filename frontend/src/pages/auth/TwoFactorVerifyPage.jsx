import { useState } from 'react';

import { getBootstrap, submitPost } from '../../app/http.js';
import { CsrfInput, Field } from '../../components/Field.jsx';
import { t, tx } from '../../i18n/index.js';
import { AuthLayout } from './AuthLayout.jsx';

/** The second sign-in step: a code from the authenticator app, or one of the recovery codes. */
export function TwoFactorVerifyPage() {
  const { data, messages } = getBootstrap();
  const [useRecoveryCode, setUseRecoveryCode] = useState(data.useRecoveryCode);
  // The server's message belongs to the kind of code that was posted.
  const error = useRecoveryCode === data.useRecoveryCode ? data.error : '';

  return (
    <AuthLayout
      title={t('twoFactorLogin.title')}
      subtitle={useRecoveryCode ? t('twoFactorLogin.subtitleRecovery') : t('twoFactorLogin.subtitleApp')}
      messages={messages}
    >
      <p className="mb-4 text-center text-sm text-muted-foreground">
        {tx('twoFactorLogin.signingInAs', { email: <bdi className="font-medium text-foreground">{data.email}</bdi> })}
      </p>

      <form method="post" action={data.urls.verify}>
        <CsrfInput />
        <input type="hidden" name="mode" value={useRecoveryCode ? 'recovery' : 'app'} />

        {useRecoveryCode ? (
          <Field
            key="recovery"
            id="code"
            name="code"
            dir="ltr"
            label={t('twoFactorLogin.recoveryCode')}
            placeholder="xxxxx-xxxxx"
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            hint={t('twoFactorLogin.recoveryHint')}
            required
            minLength={10}
            maxLength={32}
            error={error}
          />
        ) : (
          <Field
            key="app"
            id="code"
            name="code"
            dir="ltr"
            label={t('twoFactorLogin.appCode')}
            placeholder="123456"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            title={t('twoFactorLogin.sixDigits')}
            required
            maxLength={6}
            error={error}
          />
        )}

        <button type="submit" className="btn btn-primary w-full">
          {t('twoFactorLogin.verify')}
        </button>
      </form>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm">
        <button
          type="button"
          className="font-medium text-primary hover:underline"
          onClick={() => setUseRecoveryCode(!useRecoveryCode)}
        >
          {useRecoveryCode ? t('twoFactorLogin.useApp') : t('twoFactorLogin.useRecovery')}
        </button>
        <button type="button" className="text-muted-foreground hover:underline" onClick={() => submitPost(data.urls.cancel)}>
          {t('common.cancel')}
        </button>
      </div>
    </AuthLayout>
  );
}
