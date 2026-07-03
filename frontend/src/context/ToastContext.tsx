import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import type { ToastCategory } from '../types';

export interface Toast {
  id: number;
  message: string;
  category: ToastCategory;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (message: string, category?: ToastCategory) => void;
  dismissToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_DURATION = 4000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, category: ToastCategory = 'info') => {
      const id = nextId.current++;
      setToasts((current) => [...current, { id, message, category }]);
      setTimeout(() => dismissToast(id), TOAST_DURATION);
    },
    [dismissToast],
  );

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>{children}</ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
