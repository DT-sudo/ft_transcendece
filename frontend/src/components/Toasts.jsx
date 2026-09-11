import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

const ToastContext = createContext(() => {});

export const useToast = () => useContext(ToastContext);

export function ToastProvider({ initialMessages = [], children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(0);

  const showToast = useCallback((level, title, description = '') => {
    const id = ++nextId.current;
    setToasts((current) => [...current, { id, level, title, description }]);
    // Errors stay up longer so there is time to read them.
    setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), level === 'error' ? 6000 : 4000);
  }, []);

  // Django flash messages arrive with the page payload; show each once (StrictMode runs effects twice).
  const flashed = useRef(false);
  useEffect(() => {
    if (flashed.current) return;
    flashed.current = true;
    for (const { level, text } of initialMessages) showToast(level, level[0].toUpperCase() + level.slice(1), text);
  }, [initialMessages, showToast]);

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className="fixed end-4 bottom-4 z-[6000] flex flex-col gap-2" aria-live="polite" aria-atomic="true">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.level}`}>
            <div className="toast-dot" aria-hidden="true" />
            <div>
              <div className="font-bold">{toast.title}</div>
              {toast.description ? <div className="mt-0.5 text-sm text-muted-foreground">{toast.description}</div> : null}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
