/**
 * Chip colours are derived from the position id rather than stored, so a new
 * position is immediately distinguishable without a migration.
 */
export function positionPalette(positionId) {
  const id = parseInt(positionId, 10);
  if (!Number.isFinite(id)) return null;

  const hue = (((id * 47) % 360) + 360) % 360;
  return {
    '--position-bg': `hsl(${hue} 80% 92%)`,
    '--position-border': `hsl(${hue} 70% 45%)`,
    '--position-fg': `hsl(${hue} 60% 20%)`,
  };
}

export function initialsFromName(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'E';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}
