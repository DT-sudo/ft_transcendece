import { formatMonth } from '../../app/dates.js';
import { getBootstrap } from '../../app/http.js';
import { useLivePageData } from '../../app/live.js';
import { AppShell } from '../../components/AppShell.jsx';
import { Avatar, presenceLabel } from '../../components/Avatar.jsx';
import { Settings } from '../../components/Icons.jsx';
import { FRIEND_EVENTS, FriendActions, PeopleCard, PersonRow } from './People.jsx';

// This person came online or left (only sent while their status is shown, to friends).
const withPersonStatus = (data, event) =>
  event.type === 'friend.status' && event.userId === data.person.id && data.person.status
    ? { ...data, person: { ...data.person, status: event.status } }
    : data;

/**
 * Someone's profile. Friends (and you) also see the email, online status and friend
 * list; the page follows that status and the friendship live.
 */
export function ProfilePage() {
  const { urls: pageUrls } = getBootstrap();
  const { person, relation, friends, urls } = useLivePageData(getBootstrap().data, FRIEND_EVENTS, withPersonStatus);
  const isSelf = relation.state === 'self';

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="side-panel-layout mt-3">
          <section className="card p-6" aria-labelledby="profileName">
            <div className="flex flex-wrap items-center gap-5">
              <Avatar name={person.fullName} src={person.avatarUrl} size="lg" online={person.status?.online} primary />
              <div className="min-w-0 flex-1">
                <h1 id="profileName" className="text-2xl font-bold">
                  {person.fullName}
                </h1>
                <p className="text-muted-foreground">{person.role}</p>
                {person.status ? <p className="mt-1 text-sm">{presenceLabel(person.status)}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                {isSelf ? (
                  <a className="btn btn-outline" href={pageUrls.settings}>
                    <Settings size={16} />
                    Edit profile
                  </a>
                ) : (
                  <FriendActions person={person} relation={relation} urls={urls} />
                )}
              </div>
            </div>

            {relation.state === 'incoming' ? (
              <p className="mt-4 text-sm text-muted-foreground">{person.fullName} sent you a friend request.</p>
            ) : null}

            {person.bio ? (
              <p className="mt-5 whitespace-pre-line">{person.bio}</p>
            ) : isSelf ? (
              <p className="mt-5 text-sm text-muted-foreground">
                No bio yet. <a className="footer-link" href={pageUrls.settings}>Add one</a> so people know who you are.
              </p>
            ) : null}

            <dl className="profile-facts mt-5">
              {person.email ? (
                <>
                  <dt>Email</dt>
                  <dd>
                    <a className="footer-link" href={`mailto:${person.email}`}>
                      {person.email}
                    </a>
                  </dd>
                </>
              ) : null}
              <dt>Member since</dt>
              <dd>{formatMonth(person.memberSince)}</dd>
              <dt>Friends</dt>
              <dd>{person.friendCount}</dd>
            </dl>
          </section>

          {friends ? (
            <PeopleCard id="profileFriends" title="Friends" empty="No friends yet.">
              {friends.map((friend) => (
                <PersonRow key={friend.id} person={friend} detail={friend.role} />
              ))}
            </PeopleCard>
          ) : null}
        </div>
      </main>
    </AppShell>
  );
}
