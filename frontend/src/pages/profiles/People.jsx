import { useState } from 'react';

import { submitPost, urlFromTemplate } from '../../app/http.js';
import { Avatar } from '../../components/Avatar.jsx';
import { Check, UserPlus } from '../../components/Icons.jsx';
import { ConfirmModal } from '../../components/Modal.jsx';

/**
 * Live events after which the Friends and profile pages re-read their data. A friend's
 * `friend.status` (online or not) is patched in place instead, with no request.
 */
export const FRIEND_EVENTS = ['friends.changed'];

// Friend actions redirect back to the page they were taken on.
const back = () => ({ next: window.location.pathname });

/** A titled card listing people, or `empty` when there are none. */
export function PeopleCard({ id, title, count, empty, children }) {
  return (
    <section className="card" aria-labelledby={id}>
      <h2 id={id} className="card-header card-title">
        {title}
        {count ? <span className="text-sm font-normal text-muted-foreground">{count}</span> : null}
      </h2>
      {children.length ? <ul>{children}</ul> : <p className="p-4 text-sm text-muted-foreground">{empty}</p>}
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
 */
export function FriendActions({ person, relation, urls, small = false }) {
  const [confirming, setConfirming] = useState(false);
  const size = small ? 'btn-sm' : '';
  const end = () => submitPost(urlFromTemplate(urls.end, relation.friendshipId), back());

  switch (relation.state) {
    case 'none':
      return (
        <button className={`btn btn-primary ${size}`} type="button" onClick={() => submitPost(urls.request, { user_id: person.id, ...back() })}>
          <UserPlus size={16} />
          Add friend
        </button>
      );
    case 'outgoing':
      return (
        <button className={`btn btn-outline ${size}`} type="button" onClick={end}>
          Cancel request
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
            <Check size={16} />
            Accept
          </button>
          <button className={`btn btn-outline ${size}`} type="button" onClick={end}>
            Decline
          </button>
        </>
      );
    case 'friends':
      return (
        <>
          <button className={`btn btn-ghost btn-icon-destructive ${size}`} type="button" onClick={() => setConfirming(true)}>
            Remove friend
          </button>
          {confirming ? (
            <ConfirmModal
              title="Remove friend"
              message={`Remove ${person.fullName} from your friends?`}
              footnote="They will no longer see your online status or your email."
              confirmText="Yes, remove"
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
