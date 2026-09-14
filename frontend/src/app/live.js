import { useEffect, useRef } from 'react';

const SOCKET_PATH = '/ws/schedule/';
const MAX_RETRY_DELAY_MS = 15000;

// One socket per page, shared by every subscriber (the header bell and the page's own live views).
const subscribers = new Set();
let socket = null;
let retryTimer = null;
let attempts = 0;
let wasLive = false;

function connect() {
  const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const current = new WebSocket(`${scheme}://${window.location.host}${SOCKET_PATH}`);
  socket = current;

  current.onopen = () => {
    subscribers.forEach((subscriber) => {
      if (wasLive) subscriber.onReconnect();
      subscriber.onOpen();
    });
    wasLive = true;
    attempts = 0;
  };

  current.onmessage = (message) => {
    const event = JSON.parse(message.data);
    subscribers.forEach((subscriber) => subscriber.onEvent(event));
  };

  current.onclose = () => {
    if (socket !== current) return; // closed on purpose when the last subscriber left
    const delay = Math.min(MAX_RETRY_DELAY_MS, 1000 * 2 ** attempts);
    attempts += 1;
    retryTimer = setTimeout(connect, delay);
  };
}

function subscribe(subscriber) {
  subscribers.add(subscriber);
  if (!socket) connect();
  else if (socket.readyState === WebSocket.OPEN) subscriber.onOpen();

  return () => {
    subscribers.delete(subscriber);
    if (subscribers.size) return;
    clearTimeout(retryTimer);
    const closing = socket;
    socket = null;
    wasLive = false;
    attempts = 0;
    closing?.close();
  };
}

/** Send `message` over the shared socket; dropped while it is not open (use `onOpen` to resend state). */
export function sendLive(message) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message));
}

/**
 * Subscribe to server-pushed events: the user's own notifications, plus schedule
 * changes and presence for managers.
 *
 * After a drop the shared socket reconnects quietly with capped exponential backoff.
 * Events sent while offline are not replayed, so `onReconnect` fires when a lost
 * connection comes back. `onOpen` fires on every connection, the first one included.
 */
export function useLiveEvents(onEvent, { onReconnect, onOpen, enabled = true } = {}) {
  const handlers = useRef({ onEvent, onReconnect, onOpen });
  useEffect(() => {
    handlers.current = { onEvent, onReconnect, onOpen };
  });

  useEffect(() => {
    if (!enabled) return undefined;
    return subscribe({
      onEvent: (event) => handlers.current.onEvent(event),
      onReconnect: () => handlers.current.onReconnect?.(),
      onOpen: () => handlers.current.onOpen?.(),
    });
  }, [enabled]);
}
