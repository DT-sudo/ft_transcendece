import { useState } from 'react';

import { useDismiss } from './hooks.js';

/** Trigger button + menu panel below it, closed by outside click or Escape. */
export function Dropdown({ trigger, children }) {
  const [open, setOpen] = useState(false);
  const containerRef = useDismiss(open, () => setOpen(false));

  return (
    <div className="dropdown" ref={containerRef}>
      {trigger({ toggle: () => setOpen((value) => !value) })}
      {open ? <div className="dropdown-menu">{children}</div> : null}
    </div>
  );
}
