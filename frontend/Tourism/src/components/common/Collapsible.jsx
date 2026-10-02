import { useState } from "react"
import { FiChevronDown } from "react-icons/fi"

/**
 * Collapsible section with smooth height animation.
 */
export default function Collapsible({ title, children, defaultOpen = false, className = "" }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className={`border border-[var(--ny-border)] rounded-xl overflow-hidden ${className}`}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left bg-gray-50 dark:bg-slate-800/50 hover:bg-gray-100 dark:hover:bg-slate-700/50 transition-colors"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-gray-900 dark:text-white">{title}</span>
        <FiChevronDown
          size={16}
          className={`text-gray-400 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
        />
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ${
          open ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}
