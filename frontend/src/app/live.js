import { useEffect, useRef, useState } from 'react';

const SOCKET_PATH = '/ws/schedule/';
const MAX_RETRY_DELAY_MS = 15000;

/**
 * Subscribe the page to server-pushed schedule events over one WebSocket.
 *
 * After a drop it reconnects with capped exponential backoff. Events sent while
 * offline are not replayed, so `onReconnect` fires when a lost connection comes
 * back. Returns 'connecting' | 'live' | 'offline'.
 */
export function useLiveEvents(onEvent, { onReconnect } = {}) {
  const handlers = useRef({ onEvent, onReconnect });
  useEffect(() => {
    handlers.current = { onEvent, onReconnect };
  });

  const [status, setStatus] = useState('connecting');

  useEffect(() => {
    let socket = null;
    let retryTimer = null;
    let attempts = 0;
    let wasLive = false;
    let stopped = false;

    const connect = () => {
      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(`${scheme}://${window.location.host}${SOCKET_PATH}`);

      socket.onopen = () => {
        if (wasLive) handlers.current.onReconnect?.();
        wasLive = true;
        attempts = 0;
        setStatus('live');
      };

      socket.onmessage = (message) => {
        let event;
        try {
          event = JSON.parse(message.data);
        } catch {
          return;
        }
        handlers.current.onEvent(event);
      };

      socket.onclose = () => {
        if (stopped) return;
        setStatus('offline');
        const delay = Math.min(MAX_RETRY_DELAY_MS, 1000 * 2 ** attempts);
        attempts += 1;
        retryTimer = setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, []);

  return status;
}
