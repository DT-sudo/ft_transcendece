const SIZES = { sm: 'size-8', header: 'size-8.5', md: 'size-10', lg: 'size-24 text-2xl' };

/** "Maya Rossi" -> "MR", "Maya" -> "MA". */
function initialsFromName(name) {
  const [first, second] = name.trim().split(/\s+/);
  return (second ? first[0] + second[0] : first.slice(0, 2)).toUpperCase();
}

/**
 * A profile picture, or the initials default when there is none. The name always sits
 * next to it, so both are hidden from screen readers.
 */
export function Avatar({ name, src, size = 'sm', primary = false }) {
  return (
    <span className={`avatar relative ${primary && !src ? 'avatar-primary' : ''} ${SIZES[size]}`}>
      {src ? <img className="avatar-image" src={src} alt="" /> : <span aria-hidden="true">{initialsFromName(name)}</span>}
    </span>
  );
}
