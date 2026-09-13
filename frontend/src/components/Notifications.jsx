import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import { Bell } from './Icons.jsx';
import { Modal } from './Modal.jsx';

const ToastContext = createContext(() => {});
const HistoryContext = createContext(null);

/** `const showToast = useToast();` then `showToast(level, title, description)`. */
export const useToast = () => useContext(ToastContext);

const MAX_HISTORY = 100;
// A repeat within this window bumps the latest history entry instead of adding a row.
const REPEAT_WINDOW_MS = 60_000;

// History lives in this browser only, one list per signed-in account.
const storageKey = (userId) => `planshift:notifications:${userId}`;

function loadHistory(userId) {
  if (!userId) return [];
  try {
    const history = JSON.parse(localStorage.getItem(storageKey(userId)));
    return Array.isArray(history) ? history : [];
  } catch {
    return [];
  }
}

function saveHistory(userId, history) {
  if (!userId) return;
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify(history));
  } catch {
    // Storage can be unavailable (private mode, quota); the history then lasts for this page only.
  }
}

function timeAgo(time) {
  const minutes = Math.floor((Date.now() - time) / 60_000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)}h ago`;
  return new Date(time).toLocaleDateString();
}

function NotificationText({ entry }) {
  return (
    <div className="min-w-0">
      <div className="font-bold">
        {entry.title}
        {entry.count > 1 ? <span className="notification-count"> ×{entry.count}</span> : null}
      </div>
      {entry.description ? <div className="mt-0.5 text-sm text-muted-foreground">{entry.description}</div> : null}
    </div>
  );
}

/**
 * Toasts plus the notification history behind the header bell. Toasts and history
 * entries are keyed by their content, so a repeat bumps a counter instead of stacking.
 */
export function ToastProvider({ initialMessages = [], userId = null, children }) {
  const [toasts, setToasts] = useState([]);
  const [history, setHistory] = useState(() => loadHistory(userId));
  const timers = useRef(new Map());

  useEffect(() => saveHistory(userId, history), [userId, history]);

  const showToast = useCallback((level, title, description = '') => {
    const key = `${level}|${title}|${description}`;
    const time = Date.now();

    setToasts((current) =>
      current.some((toast) => toast.key === key)
        ? current.map((toast) => (toast.key === key ? { ...toast, count: toast.count + 1 } : toast))
        : [...current, { key, level, title, description, count: 1 }],
    );
    // Errors stay up longer so there is time to read them; a repeat restarts the clock.
    clearTimeout(timers.current.get(key));
    timers.current.set(
      key,
      setTimeout(() => setToasts((current) => current.filter((toast) => toast.key !== key)), level === 'error' ? 6000 : 4000),
    );

    setHistory((current) => {
      const [latest, ...rest] = current;
      if (latest?.key === key && time - latest.time < REPEAT_WINDOW_MS) {
        return [{ ...latest, count: latest.count + 1, time, read: false }, ...rest];
      }
      const entry = { id: `${time}-${key}`, key, level, title, description, count: 1, time, read: false };
      return [entry, ...current].slice(0, MAX_HISTORY);
    });
  }, []);

  // Django flash messages arrive with the page payload; show each once (StrictMode runs effects twice).
  const flashed = useRef(false);
  useEffect(() => {
    if (flashed.current) return;
    flashed.current = true;
    for (const { level, text } of initialMessages) showToast(level, level[0].toUpperCase() + level.slice(1), text);
  }, [initialMessages, showToast]);

  const center = useMemo(
    () => ({
      history,
      markAllRead: () => setHistory((current) => current.map((entry) => ({ ...entry, read: true }))),
      clear: () => setHistory([]),
    }),
    [history],
  );

  return (
    <ToastContext.Provider value={showToast}>
      <HistoryContext.Provider value={center}>
        {children}
        <div className="fixed end-4 bottom-4 z-[6000] flex flex-col gap-2" aria-live="polite" aria-atomic="true">
          {toasts.map((toast) => (
            <div key={toast.key} className={`toast toast-${toast.level}`}>
              <div className="toast-dot" aria-hidden="true" />
              <NotificationText entry={toast} />
            </div>
          ))}
        </div>
      </HistoryContext.Provider>
    </ToastContext.Provider>
  );
}

/** Header bell with an unread badge; opens the notification history. */
export function NotificationBell() {
  const { history, markAllRead, clear } = useContext(HistoryContext);
  const [open, setOpen] = useState(false);
  const unread = history.filter((entry) => !entry.read).length;

  return (
    <>
      <button
        className="btn btn-ghost btn-icon relative"
        type="button"
        aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'}
        onClick={() => {
          setOpen(true);
          markAllRead();
        }}
      >
        <Bell />
        {unread ? <span className="notification-badge">{unread > 99 ? '99+' : unread}</span> : null}
      </button>

      {/* Portalled: the sticky header is a stacking context the modal must not be trapped in. */}
      {open
        ? createPortal(
            <Modal
              title="Notifications"
              onClose={() => setOpen(false)}
              footer={
                history.length ? (
                  <button className="btn btn-outline" type="button" onClick={clear}>
                    Clear history
                  </button>
                ) : null
              }
            >
              {history.length ? (
                <ul className="modal-body p-0">
                  {history.map((entry) => (
                    <li key={entry.id} className={`notification-item toast-${entry.level}`}>
                      <div className="toast-dot" aria-hidden="true" />
                      <NotificationText entry={entry} />
                      <time className="ms-auto shrink-0 text-xs text-muted-foreground" dateTime={new Date(entry.time).toISOString()}>
                        {timeAgo(entry.time)}
                      </time>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="modal-body text-center text-sm text-muted-foreground">No notifications yet.</p>
              )}
            </Modal>,
            document.body,
          )
        : null}
    </>
  );
}
