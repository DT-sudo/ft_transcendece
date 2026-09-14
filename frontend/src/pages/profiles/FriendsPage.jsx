import { getBootstrap } from '../../app/http.js';
import { timeAgo } from '../../app/dates.js';
import { useLivePageData } from '../../app/live.js';
import { AppShell } from '../../components/AppShell.jsx';
import { presenceLabel } from '../../components/Avatar.jsx';
import { CsrfInput } from '../../components/Field.jsx';
import { UserPlus } from '../../components/Icons.jsx';
import { FRIEND_EVENTS, FriendActions, PeopleCard, PersonRow } from './People.jsx';

// A friend came online or left: move their dot without re-reading the page.
const withFriendStatus = (data, event) =>
  event.type === 'friend.status'
    ? { ...data, friends: data.friends.map((friend) => (friend.id === event.userId ? { ...friend, status: event.status } : friend)) }
    : data;

function FriendRow({ person, detail, urls }) {
  return (
    <PersonRow person={person} online={person.status?.online} detail={detail}>
      <FriendActions person={person} relation={person.relation} urls={urls} small />
    </PersonRow>
  );
}

/** Friends with their live online status, requests to answer, and requests waiting on others. */
export function FriendsPage() {
  const { friends, incoming, outgoing, urls } = useLivePageData(getBootstrap().data, FRIEND_EVENTS, withFriendStatus);
  const online = friends.filter((friend) => friend.status.online).length;

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <div className="card page-toolbar-card">
          <form className="flex flex-wrap items-center gap-2" method="post" action={urls.request}>
            <CsrfInput />
            <label className="form-label mb-0" htmlFor="friendEmail">
              Add a friend by email
            </label>
            <input
              id="friendEmail"
              name="email"
              type="email"
              className="form-input w-72 max-w-full"
              placeholder="colleague@example.com"
              autoComplete="off"
              required
            />
            <button className="btn btn-primary" type="submit">
              <UserPlus size={16} />
              Send request
            </button>
          </form>
        </div>

        <div className="side-panel-layout mt-3">
          <PeopleCard
            id="friendsList"
            title="Friends"
            count={friends.length ? `${online} of ${friends.length} online` : ''}
            empty="No friends yet. Add a colleague by their email address above."
          >
            {friends.map((friend) => (
              <FriendRow key={friend.id} person={friend} urls={urls} detail={`${friend.role} · ${presenceLabel(friend.status)}`} />
            ))}
          </PeopleCard>

          <div className="flex flex-col gap-3">
            <PeopleCard id="incomingRequests" title="Friend requests" empty="No requests to answer.">
              {incoming.map((request) => (
                <FriendRow key={request.id} person={request} urls={urls} detail={`${request.role} · ${timeAgo(request.sentAt)}`} />
              ))}
            </PeopleCard>

            <PeopleCard id="outgoingRequests" title="Sent requests" empty="No requests waiting for an answer.">
              {outgoing.map((request) => (
                <FriendRow key={request.id} person={request} urls={urls} detail={`Sent ${timeAgo(request.sentAt)}`} />
              ))}
            </PeopleCard>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
