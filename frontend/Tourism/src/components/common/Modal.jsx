import { useEffect, useId, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiX } from "react-icons/fi"

export default function Modal({ isOpen, onClose, title, children, maxWidth = "max-w-xl" }) {
  const titleId = useId()
  const dialogRef = useRef(null)
  const previousFocusRef = useRef(null)

  // Escape closes and background scroll is locked while open. Focus moves into
  // the dialog and returns to the invoking control when it closes.
  useEffect(() => {
    if (!isOpen) return undefined
    const onKey = (event) => {
      if (event.key === "Escape") {
        onClose?.()
        return
      }
      if (event.key !== "Tab" || !dialogRef.current) return
      const focusable = [...dialogRef.current.querySelectorAll("button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])")].filter((element) => element.offsetParent !== null)
      if (!focusable.length) {
        event.preventDefault()
        dialogRef.current.focus()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    window.addEventListener("keydown", onKey)
    previousFocusRef.current = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    const focusTimer = window.setTimeout(() => dialogRef.current?.focus(), 0)
    return () => {
      window.clearTimeout(focusTimer)
      window.removeEventListener("keydown", onKey)
      document.body.style.overflow = previousOverflow
      if (previousFocusRef.current instanceof HTMLElement) previousFocusRef.current.focus()
    }
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="ny-modal-layer fixed inset-0 flex items-center justify-center overflow-y-auto bg-black/75 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose?.() }}>
          <motion.div
            ref={dialogRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ duration: 0.2 }}
            className={`my-auto max-h-[90dvh] w-full ${maxWidth} space-y-4 overflow-y-auto rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-white p-6 shadow-[var(--ny-shadow-elevated)] sm:p-8`}
          >
            <div className="flex items-center justify-between border-b border-[var(--ny-border)] pb-3">
              <h3 id={titleId} className="text-lg font-bold text-[var(--ny-text)]">{title}</h3>
              <button
                type="button"
                onClick={onClose}
                className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] text-[var(--ny-text-muted)] transition-colors hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"
                aria-label="Close dialog"
              >
                <FiX size={18} aria-hidden="true" />
              </button>
            </div>
            <div>{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
