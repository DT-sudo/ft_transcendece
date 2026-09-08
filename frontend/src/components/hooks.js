import { useEffect, useLayoutEffect, useRef } from 'react';

import { pushLayer } from './escape.js';

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

/** Publish an element's measured height as a CSS custom property on :root. */
export function usePublishedHeight(cssVariable) {
  const ref = useRef(null);

  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return undefined;

    const sync = () => {
      const height = node.getBoundingClientRect().height;
      document.documentElement.style.setProperty(cssVariable, `${height}px`);
    };

    sync();
    const observer = new ResizeObserver(sync);
    observer.observe(node);
    window.addEventListener('resize', sync);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', sync);
    };
  }, [cssVariable]);

  return ref;
}

/** Re-run a callback on viewport resize (trailing debounce). */
export function useOnResize(callback) {
  const handler = useRef(callback);
  handler.current = callback;

  useEffect(() => {
    let timer;
    const onResize = () => {
      clearTimeout(timer);
      timer = setTimeout(() => handler.current(), 50);
    };

    window.addEventListener('resize', onResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', onResize);
    };
  }, []);
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
