import { useEffect, useRef } from "react"
import { FiX } from "react-icons/fi"

/**
 * Accessible modal dialog with focus trap, escape to close,
 * and backdrop click to dismiss.
 */
export default function Modal({ open, onClose, title, children, size = "md", className = "" }) {
  const dialogRef = useRef(null)
  const previousFocus = useRef(null)

  useEffect(() => {
    if (open) {
      previousFocus.current = document.activeElement
      dialogRef.current?.focus()
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
      previousFocus.current?.focus()
    }
    return () => { document.body.style.overflow = "" }
  }, [open])

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === "Escape") onClose()
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
  }

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div
        ref={dialogRef}
        tabIndex={-1}
        className={`relative w-full ${sizeClasses[size] || sizeClasses.md} rounded-2xl bg-white dark:bg-slate-800 shadow-2xl border border-gray-200 dark:border-slate-700 p-6 outline-none ${className}`}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            aria-label="Close dialog"
          >
            <FiX size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
