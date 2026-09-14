import { formatMonth } from '../../app/dates.js';
import { getBootstrap } from '../../app/http.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Avatar } from '../../components/Avatar.jsx';
import { Settings } from '../../components/Icons.jsx';

/** Someone's profile: picture, role, bio and email. You see your own, and managers see their employees'. */
export function ProfilePage() {
  const { urls: pageUrls, data } = getBootstrap();
  const { person, relation } = data;
  const isSelf = relation.state === 'self';

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <section className="card mt-3 p-6" aria-labelledby="profileName">
          <div className="flex flex-wrap items-center gap-5">
            <Avatar name={person.fullName} src={person.avatarUrl} size="lg" primary />
            <div className="min-w-0 flex-1">
              <h1 id="profileName" className="text-2xl font-bold">
                {person.fullName}
              </h1>
              <p className="text-muted-foreground">{person.role}</p>
            </div>
            {isSelf ? (
              <a className="btn btn-outline" href={pageUrls.settings}>
                <Settings size={16} />
                Edit profile
              </a>
            ) : null}
          </div>

          {person.bio ? (
            <p className="mt-5 whitespace-pre-line">{person.bio}</p>
          ) : isSelf ? (
            <p className="mt-5 text-sm text-muted-foreground">
              No bio yet. <a className="footer-link" href={pageUrls.settings}>Add one</a> so people know who you are.
            </p>
          ) : null}

          <dl className="profile-facts mt-5">
            <dt>Email</dt>
            <dd>
              <a className="footer-link" href={`mailto:${person.email}`}>
                {person.email}
              </a>
            </dd>
            <dt>Member since</dt>
            <dd>{formatMonth(person.memberSince)}</dd>
          </dl>
        </section>
      </main>
    </AppShell>
  );
}
