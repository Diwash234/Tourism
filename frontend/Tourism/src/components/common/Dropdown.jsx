import { useState, useRef, useEffect } from "react"
import { FiChevronDown } from "react-icons/fi"

/**
 * Accessible dropdown menu with keyboard navigation,
 * outside click to close, and focus management.
 */
export default function Dropdown({ trigger, items, align = "right", className = "" }) {
  const [open, setOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const containerRef = useRef(null)
  const itemRefs = useRef([])

  useEffect(() => {
    if (!open) return undefined
    const onDown = (e) => {
      if (!containerRef.current?.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => {
      if (e.key === "Escape") { setOpen(false); return }
      if (e.key === "ArrowDown") {
        e.preventDefault()
        const next = Math.min(focusedIndex + 1, items.length - 1)
        setFocusedIndex(next)
        itemRefs.current[next]?.focus()
      }
      if (e.key === "ArrowUp") {
        e.preventDefault()
        const prev = Math.max(focusedIndex - 1, 0)
        setFocusedIndex(prev)
        itemRefs.current[prev]?.focus()
      }
    }
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open, focusedIndex, items.length])

  const handleItemClick = (item, index) => {
    item.onClick?.()
    setOpen(false)
    setFocusedIndex(-1)
  }

  return (
    <div ref={containerRef} className={`relative inline-block ${className}`}>
      <div onClick={() => { setOpen(v => !v); setFocusedIndex(-1) }}>
        {typeof trigger === "string" ? (
          <button
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            aria-haspopup="menu"
            aria-expanded={open}
          >
            {trigger}
            <FiChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        ) : trigger}
      </div>

      {open && (
        <div
          role="menu"
          className={`absolute z-50 mt-1 min-w-[180px] rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl py-1 ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {items.map((item, i) => (
            <button
              key={i}
              ref={el => itemRefs.current[i] = el}
              type="button"
              role="menuitem"
              onClick={() => handleItemClick(item, i)}
              onFocus={() => setFocusedIndex(i)}
              className={`flex w-full items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                focusedIndex === i ? "bg-gray-100 dark:bg-slate-700" : ""
              } ${
                item.danger
                  ? "text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                  : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700"
              }`}
            >
              {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
