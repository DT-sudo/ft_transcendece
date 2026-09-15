import { getBootstrap } from '../../app/http.js';
import { CsrfInput, Field } from '../../components/Field.jsx';
import { t } from '../../i18n/index.js';
import { AuthLayout, FormError } from './AuthLayout.jsx';

/** Native form: the browser checks required/type, Django validates and re-renders field errors. */
export function LoginPage() {
  const { data, messages } = getBootstrap();

  return (
    <AuthLayout title={t('login.title')} subtitle={t('login.subtitle')} messages={messages}>
      {data.showDemo ? (
        <div className="mt-4">
          <a className="btn btn-outline w-full" href={data.urls.demoAdmin}>
            {t('login.demoAdmin')}
          </a>
          <a className="btn btn-outline mt-3 w-full" href={data.urls.demoManager}>
            {t('login.demoManager')}
          </a>
          <a className="btn btn-outline mt-3 w-full" href={data.urls.demoEmployee}>
            {t('login.demoEmployee')}
          </a>

          <div className="my-6 flex items-center">
            <div className="h-px flex-1 bg-border" />
            <span className="px-4 text-xs uppercase text-muted-foreground">{t('common.or')}</span>
            <div className="h-px flex-1 bg-border" />
          </div>
        </div>
      ) : null}

      <FormError message={data.error} />

      <form className="mt-3" method="post" action={data.urls.login}>
        <CsrfInput />

        <Field
          id="email"
          name="username"
          type="email"
          dir="ltr"
          label={t('login.email')}
          placeholder={t('login.emailPlaceholder')}
          autoComplete="email"
          required
          defaultValue={data.email}
          error={data.fieldErrors.email}
        />

        <Field
          id="password"
          name="password"
          type="password"
          label={t('login.password')}
          placeholder={t('login.passwordPlaceholder')}
          autoComplete="current-password"
          required
          error={data.fieldErrors.password}
        />

        <button type="submit" className="btn btn-primary w-full">
          {t('login.submit')}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        {t('login.newHere')}{' '}
        <a className="font-medium text-primary hover:underline" href={data.urls.signup}>
          {t('login.createManager')}
        </a>
      </p>
    </AuthLayout>
  );
}
