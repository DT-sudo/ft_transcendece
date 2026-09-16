import { getBootstrap } from '../../app/http.js';
import { timeAgo } from '../../app/dates.js';
import { useLivePageData } from '../../app/live.js';
import { AppShell } from '../../components/AppShell.jsx';
import { presenceLabel } from '../../components/Avatar.jsx';
import { t } from '../../i18n/index.js';
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

/** Everyone but yourself and admins. No online status here: that stays for friends only. */
function ColleagueRow({ person, urls }) {
  return (
    <PersonRow person={person} detail={person.role}>
      <FriendActions person={person} relation={person.relation} urls={urls} small />
    </PersonRow>
  );
}

/** The colleague directory (send a request from here), friends with their live online status,
 * requests to answer, and requests waiting on others. */
export function FriendsPage() {
  const { friends, incoming, outgoing, colleagues, urls } = useLivePageData(getBootstrap().data, FRIEND_EVENTS, withFriendStatus);
  const online = friends.filter((friend) => friend.status.online).length;

  return (
    <AppShell>
      <main className="p-4 pt-0">
        <PeopleCard id="colleaguesList" title={t('friends.colleagues')} count={colleagues.length ? String(colleagues.length) : ''} empty={t('friends.noColleagues')}>
          {colleagues.map((person) => (
            <ColleagueRow key={person.id} person={person} urls={urls} />
          ))}
        </PeopleCard>

        <div className="side-panel-layout mt-3">
          <PeopleCard
            id="friendsList"
            title={t('friends.friends')}
            count={friends.length ? t('friends.online', { online, total: friends.length }) : ''}
            empty={t('friends.noFriends')}
          >
            {friends.map((friend) => (
              <FriendRow key={friend.id} person={friend} urls={urls} detail={`${friend.role} · ${presenceLabel(friend.status)}`} />
            ))}
          </PeopleCard>

          <div className="flex flex-col gap-3">
            <PeopleCard id="incomingRequests" title={t('friends.requests')} empty={t('friends.noRequests')}>
              {incoming.map((request) => (
                <FriendRow key={request.id} person={request} urls={urls} detail={`${request.role} · ${timeAgo(request.sentAt)}`} />
              ))}
            </PeopleCard>

            <PeopleCard id="outgoingRequests" title={t('friends.sentRequests')} empty={t('friends.noSentRequests')}>
              {outgoing.map((request) => (
                <FriendRow key={request.id} person={request} urls={urls} detail={t('friends.sentAgo', { time: timeAgo(request.sentAt) })} />
              ))}
            </PeopleCard>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
