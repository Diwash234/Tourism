import { FiCheckCircle, FiXCircle, FiAlertTriangle, FiInfo, FiX } from "react-icons/fi"

// This module used to carry a SECOND, module-local ToastContext together with
// its own ToastProvider/useToast. Nothing ever mounted that provider (main.jsx
// mounts context/ToastContext.jsx's ToastProvider), so every component that
// imported { useToast } from here threw
// "useToast must be used within ToastProvider" at runtime and took down the
// whole page via the ErrorBoundary. All consumers now use hooks/useToast,
// which reads the provider that is actually mounted, and this file only
// exports the presentational Toast used to render a single toast.
export default function Toast({ message, type = "info", onDismiss }) {
  const icons = {
    success: <FiCheckCircle size={18} className="text-emerald-500" />,
    error: <FiXCircle size={18} className="text-red-500" />,
    warning: <FiAlertTriangle size={18} className="text-amber-500" />,
    info: <FiInfo size={18} className="text-blue-500" />,
  }

  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-lg animate-in slide-in-from-right"
      role="alert"
    >
      {icons[type] || icons.info}
      <p className="flex-1 text-sm text-gray-700 dark:text-gray-300">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="p-1 rounded text-gray-400 hover:text-gray-600"
          aria-label="Dismiss"
        >
          <FiX size={14} />
        </button>
      )}
    </div>
  )
}
