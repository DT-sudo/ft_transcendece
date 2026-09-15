import { useState } from 'react';

import { getBootstrap } from '../app/http.js';
import { changeLanguage, t, useLanguage } from '../i18n/index.js';
import { Globe } from './Icons.jsx';
import { useToast } from './Notifications.jsx';

/** Picks the language; the page switches in place, direction included. Each language is named in itself. */
export function LanguageSwitcher({ id = 'languageSwitcher', showLabel = false }) {
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
      <label className={showLabel ? 'form-label mb-0' : 'sr-only'} htmlFor={id}>
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
