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

/**
 * A colleague and the buttons their relation allows. Only friends carry a `status`, so only
 * their rows get the online dot - the directory shows none.
 */
function ColleagueRow({ person, detail, urls }) {
  return (
    <PersonRow person={person} online={person.status?.online} detail={detail}>
      <FriendActions person={person} relation={person.relation} urls={urls} small />
    </PersonRow>
  );
}

/** The colleague directory (send a request from here), friends with their live online status,
 * requests to answer, and requests waiting on others. */
export function FriendsPage() {
  const { friends, incoming, outgoing, colleagues, urls } = useLivePageData(FRIEND_EVENTS, withFriendStatus);
  const online = friends.filter((friend) => friend.status.online).length;

  return (
    <AppShell>
      <main className="p-4">
        <div className="colleagues-layout">
          <PeopleCard
            id="colleaguesList"
            title={t('friends.colleagues')}
            count={colleagues.length ? String(colleagues.length) : ''}
            empty={t('friends.noColleagues')}
          >
            {colleagues.map((person) => (
              <ColleagueRow key={person.id} person={person} urls={urls} detail={person.role} />
            ))}
          </PeopleCard>

          <PeopleCard
            id="friendsList"
            title={t('friends.friends')}
            count={friends.length ? t('friends.online', { online, total: friends.length }) : ''}
            empty={t('friends.noFriends')}
          >
            {friends.map((friend) => (
              <ColleagueRow key={friend.id} person={friend} urls={urls} detail={`${friend.role} · ${presenceLabel(friend.status)}`} />
            ))}
          </PeopleCard>

          <div className="flex flex-col gap-3">
            <PeopleCard id="incomingRequests" title={t('friends.requests')} empty={t('friends.noRequests')} short>
              {incoming.map((request) => (
                <ColleagueRow key={request.id} person={request} urls={urls} detail={`${request.role} · ${timeAgo(request.sentAt)}`} />
              ))}
            </PeopleCard>

            <PeopleCard id="outgoingRequests" title={t('friends.sentRequests')} empty={t('friends.noSentRequests')} short>
              {outgoing.map((request) => (
                <ColleagueRow key={request.id} person={request} urls={urls} detail={t('friends.sentAgo', { time: timeAgo(request.sentAt) })} />
              ))}
            </PeopleCard>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
