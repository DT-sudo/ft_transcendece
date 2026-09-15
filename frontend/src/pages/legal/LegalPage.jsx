import { getBootstrap } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { t } from '../../i18n/index.js';

/** Renders a Privacy Policy / Terms of Service document, which the server sends in the reader's language. */
export function LegalPage() {
  const { document } = getBootstrap().data;

  return (
    <AppShell>
      <main className="legal-page">
        <h1>{document.title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{t('legal.lastUpdated', { date: document.updated })}</p>

        <div className="legal-section mt-6">
          {document.intro.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>

        {document.sections.map((section) => (
          <section className="legal-section" key={section.heading}>
            <h2>{section.heading}</h2>
            {(section.paragraphs || []).map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
            {section.bullets ? (
              <ul>
                {section.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            ) : null}
          </section>
        ))}
      </main>
    </AppShell>
  );
}
