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

/**
 * Call `callback` every `delayMs` while the tab is visible (paused in
 * background tabs to avoid wasted requests). Used for the analytics
 * dashboard's "real-time" polling refresh.
 */
export function useVisiblePolling(callback, delayMs) {
  const handler = useRef(callback);
  handler.current = callback;

  useEffect(() => {
    if (!delayMs) return undefined;

    let timer = null;
    const tick = () => {
      if (document.visibilityState === 'visible') handler.current();
    };
    const start = () => {
      stop();
      timer = window.setInterval(tick, delayMs);
    };
    const stop = () => {
      if (timer) window.clearInterval(timer);
      timer = null;
    };

    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        tick();
        start();
      } else {
        stop();
      }
    };

    start();
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      stop();
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [delayMs]);
}
