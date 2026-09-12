import { useEffect, useRef, useState } from 'react';

/**
 * Tracks a container element's rendered pixel width. Charts use this to size
 * their SVG viewBox to the real box (height fixed via CSS, width == this),
 * so there is no non-uniform stretch and no letterboxing at any screen size.
 */
export function useChartWidth(defaultWidth = 640) {
  const ref = useRef(null);
  const [width, setWidth] = useState(defaultWidth);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;

    const observer = new ResizeObserver((entries) => {
      const measured = entries[0]?.contentRect.width;
      if (measured) setWidth(Math.max(120, Math.round(measured)));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, width];
}
