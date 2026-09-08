import { getBootstrap } from '../../app/bootstrap.js';
import { AppShell } from '../../components/AppShell.jsx';

/**
 * Renders a Privacy Policy / Terms of Service document from the structured
 * payload in `apps/legal/documents.py`. Bold runs are written as **text** in
 * the source so the prose stays readable there; this splits them out rather
 * than shipping a markdown parser for one construct.
 */
function RichText({ text }) {
  const parts = String(text).split(/\*\*(.+?)\*\*/g);
  return (
    <>
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <strong key={index} className="font-semibold">
            {part}
          </strong>
        ) : (
          part
        ),
      )}
    </>
  );
}

function Section({ section }) {
  return (
    <section className="legal-section">
      <h2>{section.heading}</h2>

      {(section.paragraphs || []).map((paragraph, index) => (
        <p key={index}>
          <RichText text={paragraph} />
        </p>
      ))}

      {section.bullets?.length ? (
        <ul>
          {section.bullets.map((bullet, index) => (
            <li key={index}>
              <RichText text={bullet} />
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

export function LegalPage() {
  const { data } = getBootstrap();
  const document = data.document || {};

  return (
    <AppShell>
      <main className="legal-page">
        <h1>{document.title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">Last updated: {document.updated}</p>

        <div className="legal-section mt-6">
          {(document.intro || []).map((paragraph, index) => (
            <p key={index} className={index ? 'mt-3' : ''}>
              <RichText text={paragraph} />
            </p>
          ))}
        </div>

        {(document.sections || []).map((section) => (
          <Section key={section.heading} section={section} />
        ))}
      </main>
    </AppShell>
  );
}
