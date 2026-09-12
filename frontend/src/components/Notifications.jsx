import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { Bell, Trash } from './Icons.jsx';
import { Modal } from './Modal.jsx';

const ToastContext = createContext(() => {});
const NotificationCenterContext = createContext(null);

/** `const showToast = useToast();` then `showToast(level, title, description)`. */
export const useToast = () => useContext(ToastContext);

/** History/unread-count/open-close, for the bell button and its panel. */
export const useNotificationCenter = () => useContext(NotificationCenterContext);

const LIFETIME_MS = { error: 5000 };
const DEFAULT_LIFETIME_MS = 3000;

// Repeats of the same notification within this window collapse into one
// entry (toast stays on screen and its counter ticks up) instead of piling
// up as separate, identical-looking toasts/history rows.
const DEDUPE_WINDOW_MS = 60_000;
const MAX_HISTORY = 200;

const historyKey = (userId) => `planshift:notifications:${userId}`;

function loadHistory(userId) {
  if (!userId) return [];
  try {
    const raw = window.localStorage.getItem(historyKey(userId));
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveHistory(userId, history) {
  if (!userId) return;
  try {
    window.localStorage.setItem(historyKey(userId), JSON.stringify(history.slice(0, MAX_HISTORY)));
  } catch {
    // Storage can be unavailable (private mode, quota) - history just won't persist.
  }
}

function signatureOf(entry) {
  return `${entry.level}|${entry.title}|${entry.description}`;
}

export function formatRelativeTime(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

/**
 * Toast popups plus a persisted notification history (bell button + panel
 * live in `NotificationBell`, wherever the page mounts it). Identical
 * notifications that happen again shortly after collapse into the existing
 * toast/history entry (count goes up) instead of stacking duplicates.
 */
export function ToastProvider({ initialMessages = [], userId = null, children }) {
  const [toasts, setToasts] = useState([]);
  const [history, setHistory] = useState(() => loadHistory(userId));
  const [isOpen, setIsOpen] = useState(false);
  const nextId = useRef(0);
  const timers = useRef(new Map());

  // Switching accounts (different userId) should load that account's own history.
  useEffect(() => {
    setHistory(loadHistory(userId));
  }, [userId]);

  useEffect(() => {
    saveHistory(userId, history);
  }, [userId, history]);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const scheduleDismiss = useCallback(
    (id, level) => {
      const timer = timers.current.get(id);
      if (timer) clearTimeout(timer);
      timers.current.set(
        id,
        setTimeout(() => dismiss(id), LIFETIME_MS[level] ?? DEFAULT_LIFETIME_MS),
      );
    },
    [dismiss],
  );

  const showToast = useCallback(
    (level, title, description = '') => {
      const normalizedLevel = level || 'info';
      const signature = `${normalizedLevel}|${title}|${description}`;
      const now = Date.now();

      // Same notification already on screen: bump its count and restart the timer
      // instead of stacking a second, visually identical toast.
      let mergedToastId = null;
      setToasts((current) => {
        const existing = current.find((toast) => signatureOf(toast) === signature);
        if (existing) {
          mergedToastId = existing.id;
          return current.map((toast) =>
            toast.id === existing.id ? { ...toast, count: toast.count + 1 } : toast,
          );
        }
        return current;
      });

      if (mergedToastId != null) {
        scheduleDismiss(mergedToastId, normalizedLevel);
      } else {
        nextId.current += 1;
        const id = nextId.current;
        setToasts((current) => [
          ...current,
          { id, level: normalizedLevel, title, description, count: 1 },
        ]);
        scheduleDismiss(id, normalizedLevel);
      }

      // History: same story, but recent repeats (even after their toast has
      // already faded) fold into the latest matching entry instead of
      // filling the history list with duplicates.
      setHistory((current) => {
        const [latest, ...rest] = current;
        if (
          latest &&
          signatureOf(latest) === signature &&
          now - new Date(latest.timestamp).getTime() < DEDUPE_WINDOW_MS
        ) {
          return [{ ...latest, count: latest.count + 1, timestamp: new Date(now).toISOString(), read: false }, ...rest];
        }
        const entry = {
          id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
          level: normalizedLevel,
          title,
          description,
          timestamp: new Date(now).toISOString(),
          count: 1,
          read: false,
        };
        return [entry, ...current].slice(0, MAX_HISTORY);
      });
    },
    [scheduleDismiss],
  );

  // Django flash messages arrive with the page payload; show each of them once.
  const flashed = useRef(false);
  useEffect(() => {
    if (flashed.current) return;
    flashed.current = true;

    for (const message of initialMessages) {
      const level = (message.level || 'info').split(' ')[0];
      showToast(level, level.charAt(0).toUpperCase() + level.slice(1), message.text || '');
    }
  }, [initialMessages, showToast]);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach((timer) => clearTimeout(timer));
  }, []);

  const open = useCallback(() => {
    setIsOpen(true);
    setHistory((current) => current.map((entry) => (entry.read ? entry : { ...entry, read: true })));
  }, []);
  const close = useCallback(() => setIsOpen(false), []);
  const clear = useCallback(() => setHistory([]), []);

  const unreadCount = useMemo(() => history.filter((entry) => !entry.read).length, [history]);

  const centerValue = useMemo(
    () => ({ history, unreadCount, isOpen, open, close, clear }),
    [history, unreadCount, isOpen, open, close, clear],
  );

  return (
    <ToastContext.Provider value={showToast}>
      <NotificationCenterContext.Provider value={centerValue}>
        {children}

        <div
          className="fixed right-4 bottom-4 z-[6000] flex flex-col gap-2"
          aria-live="polite"
          aria-atomic="true"
        >
          {toasts.map((toast) => (
            <button
              key={toast.id}
              type="button"
              className={`toast toast-${toast.level} toast-clickable`}
              onClick={() => {
                dismiss(toast.id);
                open();
              }}
              title="View notification history"
            >
              <div className="toast-dot" aria-hidden="true" />
              <div className="min-w-0 flex-1 text-left">
                <div className="font-bold">
                  {toast.title}
                  {toast.count > 1 ? <span className="toast-count"> ×{toast.count}</span> : null}
                </div>
                {toast.description ? (
                  <div className="mt-0.5 text-sm text-muted-foreground">{toast.description}</div>
                ) : null}
              </div>
            </button>
          ))}
        </div>

        {isOpen ? <NotificationHistoryModal onClose={close} history={history} onClear={clear} /> : null}
      </NotificationCenterContext.Provider>
    </ToastContext.Provider>
  );
}

function NotificationHistoryModal({ onClose, history, onClear }) {
  return (
    <Modal title="Notifications" onClose={onClose} maxWidth="480px">
      <div className="modal-body notification-history">
        {history.length === 0 ? (
          <div className="py-6 text-center text-sm text-muted-foreground">No notifications yet.</div>
        ) : (
          <ul className="notification-history-list">
            {history.map((entry) => (
              <li key={entry.id} className={`notification-history-item toast-${entry.level}`}>
                <div className="toast-dot" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium">
                    {entry.title}
                    {entry.count > 1 ? <span className="toast-count"> ×{entry.count}</span> : null}
                  </div>
                  {entry.description ? (
                    <div className="mt-0.5 text-sm text-muted-foreground">{entry.description}</div>
                  ) : null}
                </div>
                <div className="shrink-0 text-xs text-muted-foreground">{formatRelativeTime(entry.timestamp)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
      {history.length > 0 ? (
        <div className="modal-footer">
          <button className="btn btn-outline" type="button" onClick={onClear}>
            <Trash size={16} />
            Clear history
          </button>
        </div>
      ) : null}
    </Modal>
  );
}

/** Bell button with an unread-count badge; opens the shared history panel. */
export function NotificationBell() {
  const center = useNotificationCenter();
  if (!center) return null;
  const { unreadCount, open } = center;

  return (
    <button
      className="btn btn-ghost btn-icon notification-bell"
      type="button"
      onClick={open}
      aria-label={unreadCount > 0 ? `Notifications (${unreadCount} unread)` : 'Notifications'}
    >
      <Bell size={18} />
      {unreadCount > 0 ? (
        <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
      ) : null}
    </button>
  );
}
