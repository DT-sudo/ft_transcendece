import { useEffect, useLayoutEffect, useRef, useState } from 'react';

import { ChevronDown } from './Icons.jsx';
import { useDismiss } from './hooks.js';

const FIXED_MENU_MIN_WIDTH = 160;

/**
 * Button + menu panel. `fixed` lifts the menu out of clipping ancestors
 * (table cells with their own scroll container) by positioning it viewport-fixed.
 */
export function Dropdown({ trigger, children, fixed = false, menuClassName = '' }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const containerRef = useDismiss(open, () => setOpen(false));

  useLayoutEffect(() => {
    if (!open || !fixed || !triggerRef.current) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const menuWidth = Math.max(menuRef.current?.offsetWidth || 0, FIXED_MENU_MIN_WIDTH);
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;

    setPosition({
      top: Math.round(rect.bottom + 6),
      left: Math.round(Math.min(Math.max(8, rect.right - menuWidth), viewportWidth - menuWidth - 8)),
    });
  }, [open, fixed]);

  useEffect(() => {
    if (!open || !fixed) return undefined;

    const close = () => setOpen(false);
    window.addEventListener('scroll', close, true);
    return () => window.removeEventListener('scroll', close, true);
  }, [open, fixed]);

  return (
    <div className="dropdown" ref={containerRef}>
      <span ref={triggerRef}>
        {trigger({ open, toggle: () => setOpen((value) => !value) })}
      </span>

      {open ? (
        <div
          ref={menuRef}
          className={`dropdown-menu ${fixed ? 'dropdown-menu-fixed' : ''} ${menuClassName}`}
          style={fixed && position ? { top: position.top, left: position.left, right: 'auto' } : undefined}
        >
          {typeof children === 'function' ? children({ close: () => setOpen(false) }) : children}
        </div>
      ) : null}
    </div>
  );
}

/** Multiselect-styled popover: an outline button that opens a panel below it. */
export function SelectPopover({
  label,
  children,
  full = false,
  disabled = false,
  ariaLabel,
  menuClassName = '',
  triggerClassName = '',
  className = '',
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useDismiss(open, () => setOpen(false));

  return (
    <div className={`multiselect ${full ? 'multiselect-full' : ''} ${className}`} ref={containerRef}>
      <button
        className={`btn btn-outline btn-sm multiselect-trigger ${triggerClassName}`}
        type="button"
        disabled={disabled}
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {label}
        <ChevronDown size={16} />
      </button>

      {open ? (
        <div className={`multiselect-menu ${menuClassName}`} role="menu" aria-label={ariaLabel}>
          {typeof children === 'function' ? children({ close: () => setOpen(false) }) : children}
        </div>
      ) : null}
    </div>
  );
}
