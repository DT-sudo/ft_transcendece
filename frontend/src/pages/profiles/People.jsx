import { useState } from 'react';

import { submitPost, urlFromTemplate } from '../../app/http.js';
import { DIRECTORY_CHANGED } from '../../app/live.js';
import { Avatar } from '../../components/Avatar.jsx';
import { Minus, Plus } from '../../components/Icons.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';
import { t } from '../../i18n/index.js';

/**
 * Live events after which the Friends and profile pages re-read their data: a friendship
 * changed, or the directory did (a colleague joined, left, or changed job). A friend's
 * `friend.status` (online or not) is patched in place instead, with no request.
 */
export const FRIEND_EVENTS = ['friends.changed', DIRECTORY_CHANGED];

// Friend actions redirect back to the page they were taken on.
const back = () => ({ next: window.location.pathname });

/**
 * A titled card listing people, or `empty` when there are none. The list scrolls inside the
 * card, so a long one never pushes the sections beside it off the screen; `short` halves the
 * height for the two cards that share a column.
 */
export function PeopleCard({ id, title, count, empty, short = false, children }) {
  return (
    <section className="card" aria-labelledby={id}>
      <h2 id={id} className="card-header card-title">
        {title}
        {count ? <span className="text-sm font-normal text-muted-foreground">{count}</span> : null}
      </h2>
      {children.length ? (
        <ul className={`people-list ${short ? 'people-list-short' : ''}`}>{children}</ul>
      ) : (
        <p className="p-4 text-sm text-muted-foreground">{empty}</p>
      )}
    </section>
  );
}

/** One person in a list: picture (with a status dot when `online` is given), linked name, a detail line, actions. */
export function PersonRow({ person, detail, online, children }) {
  return (
    <li className="person-row">
      <Avatar name={person.fullName} src={person.avatarUrl} size="md" online={online} />
      <div className="min-w-0 flex-1">
        <a className="person-name" href={person.profileUrl}>
          {person.fullName}
        </a>
        <div className="truncate text-xs text-muted-foreground">{detail}</div>
      </div>
      {children ? <div className="flex shrink-0 flex-wrap justify-end gap-2">{children}</div> : null}
    </li>
  );
}

/**
 * The buttons one relation allows: add, cancel a sent request, accept or decline a
 * received one, or unfriend (after a confirmation).
 *
 * Two icons carry the whole set, so the direction of a button is readable before its
 * label is: a plus gains a friend, a minus gives one up. Removing a friend is the one
 * action that cannot be undone from the same list, so it is the one in destructive red.
 */
export function FriendActions({ person, relation, urls, small = false }) {
  const [confirming, setConfirming] = useState(false);
  const size = small ? 'btn-sm' : '';
  const end = () => submitPost(urlFromTemplate(urls.end, relation.friendshipId), back());

  switch (relation.state) {
    case 'none':
      return (
        <button className={`btn btn-primary ${size}`} type="button" onClick={() => submitPost(urls.request, { user_id: person.id, ...back() })}>
          <Plus size={16} />
          {t('friends.add')}
        </button>
      );
    case 'outgoing':
      return (
        <button className={`btn btn-outline ${size}`} type="button" onClick={end}>
          <Minus size={16} />
          {t('friends.cancelRequest')}
        </button>
      );
    case 'incoming':
      return (
        <>
          <button
            className={`btn btn-primary ${size}`}
            type="button"
            onClick={() => submitPost(urlFromTemplate(urls.accept, relation.friendshipId), back())}
          >
            <Plus size={16} />
            {t('friends.accept')}
          </button>
          <button className={`btn btn-outline ${size}`} type="button" onClick={end}>
            <Minus size={16} />
            {t('friends.decline')}
          </button>
        </>
      );
    case 'friends':
      return (
        <>
          <button className={`btn btn-destructive ${size}`} type="button" onClick={() => setConfirming(true)}>
            <Minus size={16} />
            {t('friends.remove')}
          </button>
          {confirming ? (
            <ConfirmModal
              title={t('friends.remove')}
              message={t('friends.removeMessage', { name: person.fullName })}
              footnote={t('friends.removeNote')}
              confirmText={t('friends.yesRemove')}
              destructive
              onCancel={() => setConfirming(false)}
              onConfirm={end}
            />
          ) : null}
        </>
      );
    default:
      return null;
  }
}
