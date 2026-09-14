import { timeAgo } from '../app/dates.js';

const SIZES = { sm: 'size-8', header: 'size-8.5', md: 'size-10', lg: 'size-24 text-2xl' };

/** "Maya Rossi" -> "MR", "Maya" -> "MA". */
function initialsFromName(name) {
  const [first, second] = name.trim().split(/\s+/);
  return (second ? first[0] + second[0] : first.slice(0, 2)).toUpperCase();
}

/**
 * A profile picture, or the initials default when there is none. The name always sits
 * next to it, so both are hidden from screen readers. `online` (true or false) adds a
 * status dot; leave it undefined where the status isn't shown.
 */
export function Avatar({ name, src, size = 'sm', online, primary = false }) {
  return (
    <span className={`avatar relative ${primary && !src ? 'avatar-primary' : ''} ${SIZES[size]}`}>
      {src ? <img className="avatar-image" src={src} alt="" /> : <span aria-hidden="true">{initialsFromName(name)}</span>}
      {online === undefined ? null : (
        <span className={`avatar-status ${online ? 'avatar-status-online' : ''}`}>
          <span className="sr-only">{online ? 'Online' : 'Offline'}</span>
        </span>
      )}
    </span>
  );
}

/** "Online", "Last seen 5 minutes ago" or "Offline", from a `{ online, lastSeen }` status. */
export function presenceLabel(status) {
  if (status.online) return 'Online';
  return status.lastSeen ? `Last seen ${timeAgo(status.lastSeen)}` : 'Offline';
}
