import { useEffect, useRef } from 'react';

/**
 * Dismissal stack. Escape closes the most recently opened layer only: a popover
 * inside a modal closes before the modal, and the top modal closes first.
 */
const layers = [];

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape' || layers.length === 0) return;
  event.preventDefault();
  layers[layers.length - 1].handler();
});

/** Register a dismissible layer; returns its depth and an unregister function. */
export function pushLayer(handler, token) {
  const layer = { handler, token };
  layers.push(layer);
  return {
    depth: layers.length,
    remove: () => {
      const index = layers.indexOf(layer);
      if (index >= 0) layers.splice(index, 1);
    },
  };
}

export function isTopLayer(token) {
  return layers.length > 0 && layers[layers.length - 1].token === token;
}

/** Close a popover on outside click or Escape. */
export function useDismiss(open, onDismiss) {
  const ref = useRef(null);
  const handler = useRef(onDismiss);
  handler.current = onDismiss;

  useEffect(() => {
    if (!open) return undefined;

    const onPointerDown = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      handler.current?.();
    };

    document.addEventListener('mousedown', onPointerDown);
    const layer = pushLayer(() => handler.current?.());

    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      layer.remove();
    };
  }, [open]);

  return ref;
}

/** Restore a fresh page when the browser serves it from the back/forward cache. */
export function useReloadOnBackForward() {
  useEffect(() => {
    const onPageShow = (event) => {
      if (event.persisted) window.location.reload();
    };
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  }, []);
}
