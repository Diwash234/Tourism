import Modal from "./Modal"

/**
 * Confirmation dialog for destructive or important actions.
 * Returns a promise-like interface via onConfirm/onCancel callbacks.
 */
export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
}) {
  const handleConfirm = () => {
    onConfirm?.()
    onClose()
  }

  const confirmClasses = {
    danger: "bg-red-600 hover:bg-red-700 text-white",
    primary: "bg-[var(--ny-green)] hover:bg-[var(--ny-emerald)] text-white",
    warning: "bg-amber-500 hover:bg-amber-600 text-white",
  }

  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">{message}</p>
      <div className="flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 rounded-lg text-sm font-semibold text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${confirmClasses[variant] || confirmClasses.primary}`}
        >
          {confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
