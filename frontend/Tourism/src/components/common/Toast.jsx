import { createContext, useContext, useState, useCallback } from "react"
import { FiCheckCircle, FiXCircle, FiAlertTriangle, FiInfo, FiX } from "react-icons/fi"

const ToastContext = createContext(null)

let toastId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = "info", duration = 4000) => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const icons = {
    success: <FiCheckCircle size={18} className="text-emerald-500" />,
    error: <FiXCircle size={18} className="text-red-500" />,
    warning: <FiAlertTriangle size={18} className="text-amber-500" />,
    info: <FiInfo size={18} className="text-blue-500" />,
  }

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-20 right-4 z-[100] flex flex-col gap-2 max-w-sm" role="region" aria-label="Notifications">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className="flex items-start gap-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-lg animate-in slide-in-from-right"
            role="alert"
          >
            {icons[toast.type] || icons.info}
            <p className="flex-1 text-sm text-gray-700 dark:text-gray-300">{toast.message}</p>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              aria-label="Dismiss"
            >
              <FiX size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error("useToast must be used within ToastProvider")
  return context
}
