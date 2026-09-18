import { getBootstrap } from '../../app/http.js';
import { EmailField, Field, FullNameField, PostForm } from '../../components/Field.jsx';
import { t, tx } from '../../i18n/index.js';
import { AuthLayout, FormError } from './AuthLayout.jsx';

/** Native form: the browser checks required/type/length, Django validates and re-renders field errors. */
export function SignUpPage() {
  const { data, messages, urls } = getBootstrap();
  const errors = data.fieldErrors;

  return (
    <AuthLayout title={t('signup.title')} subtitle={t('signup.subtitle')} messages={messages}>
      <FormError message={data.error} />

      <PostForm className="mt-3" action={data.urls.signup}>

        <FullNameField
          id="fullName"
          placeholder={t('signup.fullNamePlaceholder')}
          defaultValue={data.values.fullName}
          error={errors.full_name}
        />

        <EmailField
          id="email"
          placeholder={t('login.emailPlaceholder')}
          hint={t('signup.emailHint')}
          defaultValue={data.values.email}
          error={errors.email}
        />

        <Field
          id="password1"
          name="password1"
          type="password"
          label={t('login.password')}
          placeholder={t('signup.passwordPlaceholder')}
          autoComplete="new-password"
          hint={t('signup.passwordHint')}
          required
          minLength={8}
          error={errors.password1}
        />

        <Field
          id="password2"
          name="password2"
          type="password"
          label={t('signup.confirmPassword')}
          placeholder={t('signup.confirmPlaceholder')}
          autoComplete="new-password"
          required
          minLength={8}
          error={errors.password2}
        />

        <button type="submit" className="btn btn-primary w-full">
          {t('signup.submit')}
        </button>
      </PostForm>

      <p className="mt-5 text-center text-xs text-muted-foreground">
        {tx('signup.agree', {
          terms: (
            <a className="underline hover:text-foreground" href={urls.terms}>
              {t('footer.terms')}
            </a>
          ),
          privacy: (
            <a className="underline hover:text-foreground" href={urls.privacy}>
              {t('footer.privacyPolicy')}
            </a>
          ),
        })}
      </p>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        {t('signup.haveAccount')}{' '}
        <a className="font-medium text-primary hover:underline" href={data.urls.login}>
          {t('signup.signIn')}
        </a>
      </p>

      <p className="mt-4 text-center text-xs text-muted-foreground">{t('signup.employeesNote')}</p>
    </AuthLayout>
  );
}
