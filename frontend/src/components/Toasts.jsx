import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

const ToastContext = createContext(() => {});

export const useToast = () => useContext(ToastContext);

const LIFETIME_MS = { error: 5000 };
const DEFAULT_LIFETIME_MS = 3000;

export function ToastProvider({ initialMessages = [], children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(0);
  const timers = useRef(new Set());

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (level, title, description = '') => {
      nextId.current += 1;
      const id = nextId.current;

      setToasts((current) => [...current, { id, level: level || 'info', title, description }]);

      const timer = setTimeout(() => dismiss(id), LIFETIME_MS[level] ?? DEFAULT_LIFETIME_MS);
      timers.current.add(timer);
    },
    [dismiss],
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
    return () => pending.forEach(clearTimeout);
  }, []);

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div
        className="fixed right-4 bottom-4 z-[6000] flex flex-col gap-2"
        aria-live="polite"
        aria-atomic="true"
      >
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.level}`}>
            <div className="toast-dot" aria-hidden="true" />
            <div>
              <div className="font-bold">{toast.title}</div>
              {toast.description ? (
                <div className="mt-0.5 text-sm text-muted-foreground">{toast.description}</div>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
