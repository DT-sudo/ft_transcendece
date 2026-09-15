import { useState } from 'react';

import { getBootstrap } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Download, ShieldCheck, Trash } from '../../components/Icons.jsx';
import { t, tx } from '../../i18n/index.js';
import { DeleteAccountModal } from './DeleteAccountModal.jsx';

/** GDPR self-service: what we hold, download a copy of it, delete the account. */
export function PrivacyCenterPage() {
  const { urls: globalUrls, data } = getBootstrap();
  const { urls, isManager, email } = data;
  const [showDelete, setShowDelete] = useState(false);

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="card page-toolbar-card">
          <div className="flex items-center gap-3">
            <ShieldCheck size={20} className="text-muted-foreground" />
            <div>
              <div className="card-title">{t('privacy.title')}</div>
              <p className="text-sm text-muted-foreground">{t('privacy.subtitle')}</p>
            </div>
          </div>
        </div>

        <div className="card mt-3 p-4">
          <div className="card-title">{t('privacy.holdTitle')}</div>
          <p className="mt-2 text-sm text-muted-foreground">
            {isManager ? t('privacy.holdManager') : t('privacy.holdEmployee')}{' '}
            {tx('privacy.holdMore', {
              policy: (
                <a className="footer-link" href={globalUrls.privacy}>
                  {t('footer.privacyPolicy')}
                </a>
              ),
            })}
          </p>
        </div>

        <div className="card mt-3 p-4">
          <div className="card-title">{t('privacy.requestTitle')}</div>
          <p className="mt-2 text-sm text-muted-foreground">{t('privacy.requestText')}</p>
          <a className="btn btn-outline mt-3" href={urls.exportData}>
            <Download size={16} />
            {t('privacy.download')}
          </a>
        </div>

        <div className="card card-danger mt-3 p-4">
          <div className="card-title">{t('privacy.deleteTitle')}</div>
          <p className="mt-2 text-sm text-muted-foreground">
            {isManager ? t('privacy.deleteManager') : t('privacy.deleteEmployee')} {t('privacy.deleteFinal')}
          </p>
          <button className="btn btn-destructive mt-3" type="button" onClick={() => setShowDelete(true)}>
            <Trash size={16} />
            {t('privacy.deleteButton')}
          </button>
        </div>
      </main>

      {showDelete ? (
        <DeleteAccountModal email={email} action={urls.deleteAccount} onClose={() => setShowDelete(false)} />
      ) : null}
    </AppShell>
  );
}
