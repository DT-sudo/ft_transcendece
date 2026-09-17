import { useState } from 'react';

import { getBootstrap } from '../app/http.js';
import { changeLanguage, t, useLanguage } from '../i18n/index.js';
import { Globe } from './Icons.jsx';
import { useToast } from './Notifications.jsx';

/** The footer's language picker - the one place the language is changed. The page switches in
 * place, direction included, and each language is named in itself. */
export function LanguageSwitcher({ id = 'languageSwitcher' }) {
  const { languages } = getBootstrap();
  const current = useLanguage();
  const showToast = useToast();
  const [busy, setBusy] = useState(false);

  const change = async (event) => {
    setBusy(true);
    try {
      await changeLanguage(event.target.value);
    } catch (error) {
      showToast('error', t('toast.error'), error.message || t('common.requestFailed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center gap-1.5">
      <Globe size={14} className="text-muted-foreground" />
      <label className="sr-only" htmlFor={id}>
        {t('language.label')}
      </label>
      <select id={id} className="form-select form-select-sm w-auto" value={current} onChange={change} disabled={busy}>
        {languages.map((option) => (
          <option key={option.code} value={option.code} lang={option.code} dir={option.dir}>
            {option.name}
          </option>
        ))}
      </select>
    </div>
  );
}
