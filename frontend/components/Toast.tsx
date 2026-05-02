"use client";

import { useEffect, useState, useCallback } from "react";
import { CheckCircle, XCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  type: ToastType;
  title: string;
  message?: string;
}

let toastId = 0;
let addToastFn: ((t: Omit<Toast, "id">) => void) | null = null;

export function toast(type: ToastType, title: string, message?: string) {
  addToastFn?.({ type, title, message });
}
toast.success = (title: string, message?: string) => toast("success", title, message);
toast.error = (title: string, message?: string) => toast("error", title, message);
toast.info = (title: string, message?: string) => toast("info", title, message);

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((t: Omit<Toast, "id">) => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== id)), 4500);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => { addToastFn = null; };
  }, [addToast]);

  const icons = { success: CheckCircle, error: XCircle, info: Info };
  const colors = {
    success: "var(--emerald)",
    error: "var(--red)",
    info: "var(--cyan)",
  };

  return (
    <div className="toast-container">
      {toasts.map((t) => {
        const Icon = icons[t.type];
        return (
          <div key={t.id} className={`toast ${t.type} slide-up`}>
            <div className="toast-icon">
              <Icon size={16} color={colors[t.type]} />
            </div>
            <div className="toast-message">
              <div className="toast-title">{t.title}</div>
              {t.message && <div className="toast-body">{t.message}</div>}
            </div>
            <button
              onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
              style={{ background: "none", border: "none", color: "var(--text-faint)", cursor: "pointer", padding: 2, display: "flex" }}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
