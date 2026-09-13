import { useState } from 'react';

import { getBootstrap } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Download, ShieldCheck, Trash } from '../../components/Icons.jsx';
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
              <div className="card-title">Privacy & my data</div>
              <p className="text-sm text-muted-foreground">
                What PlanShift holds about your account, and your GDPR rights over it.
              </p>
            </div>
          </div>
        </div>

        <div className="card mt-3 p-4">
          <div className="card-title">What we hold about you</div>
          <p className="mt-2 text-sm text-muted-foreground">
            Your name, email, employee ID and role
            {isManager ? ', and the shifts you have created.' : ', plus your shift assignments and the days you have marked yourself unavailable.'}{' '}
            See the full <a className="footer-link" href={globalUrls.privacy}>Privacy Policy</a> for why each piece is
            collected and who can see it.
          </p>
        </div>

        <div className="card mt-3 p-4">
          <div className="card-title">Request your data</div>
          <p className="mt-2 text-sm text-muted-foreground">
            Download everything above as a single JSON file - readable in any text editor or spreadsheet tool that
            imports JSON. We also email you a confirmation so you know if a copy of your data was ever downloaded
            without you.
          </p>
          <a className="btn btn-outline mt-3" href={urls.exportData}>
            <Download size={16} />
            Download my data
          </a>
        </div>

        <div className="card card-danger mt-3 p-4">
          <div className="card-title">Delete your account</div>
          <p className="mt-2 text-sm text-muted-foreground">
            {isManager
              ? "Permanently deletes your account. If you've created shifts still on the schedule, reassign or " +
                'remove them first - the schedule keeps a record of who created a published shift, so it can\u2019t ' +
                'be deleted out from under it.'
              : 'Permanently deletes your account, your shift assignments and your unavailability records.'}{' '}
            This cannot be undone and there is no archive copy. A confirmation email is sent once it's done.
          </p>
          <button className="btn btn-destructive mt-3" type="button" onClick={() => setShowDelete(true)}>
            <Trash size={16} />
            Delete my account
          </button>
        </div>
      </main>

      {showDelete ? (
        <DeleteAccountModal email={email} action={urls.deleteAccount} onClose={() => setShowDelete(false)} />
      ) : null}
    </AppShell>
  );
}
