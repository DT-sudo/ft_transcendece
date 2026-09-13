import { useState } from 'react';

import { useDismiss } from './hooks.js';

/** Trigger button + menu panel below it, closed by picking an item, outside click or Escape. */
export function Dropdown({ trigger, children }) {
  const [open, setOpen] = useState(false);
  const containerRef = useDismiss(open, () => setOpen(false));

  return (
    <div className="dropdown" ref={containerRef}>
      {trigger({ toggle: () => setOpen((value) => !value) })}
      {open ? (
        <div className="dropdown-menu" onClick={() => setOpen(false)}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
