import { STATUS_OPTIONS } from '../app/shifts.js';

/** "Draft" (outlined) or "Published" (green) badge for a shift's status. */
export function ShiftStatusBadge({ status }) {
  const label = STATUS_OPTIONS.find((option) => option.id === status)?.name ?? status;
  return <span className={`badge ${status === 'draft' ? 'badge-outline' : 'badge-success'}`}>{label}</span>;
}
