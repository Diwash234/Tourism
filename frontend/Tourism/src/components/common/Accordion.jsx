import { useState } from "react"
import { FiChevronDown } from "react-icons/fi"

/**
 * Accessible accordion with smooth expand/collapse animation.
 * Supports single and multiple open items.
 */
export default function Accordion({ items, allowMultiple = false, className = "" }) {
  const [openIndexes, setOpenIndexes] = useState(new Set())

  const toggle = (index) => {
    setOpenIndexes(prev => {
      const next = new Set(allowMultiple ? prev : [])
      if (prev.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  return (
    <div className={`divide-y divide-[var(--ny-border)] border border-[var(--ny-border)] rounded-xl overflow-hidden ${className}`}>
      {items.map((item, i) => {
        const isOpen = openIndexes.has(i)
        return (
          <div key={i}>
            <button
              type="button"
              onClick={() => toggle(i)}
              aria-expanded={isOpen}
              aria-controls={`accordion-panel-${i}`}
              id={`accordion-button-${i}`}
              className="flex w-full items-center justify-between px-4 py-3.5 text-left bg-white dark:bg-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              <span className="text-sm font-semibold text-gray-900 dark:text-white">{item.title}</span>
              <FiChevronDown
                size={18}
                className={`text-gray-400 transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
              />
            </button>
            <div
              id={`accordion-panel-${i}`}
              role="region"
              aria-labelledby={`accordion-button-${i}`}
              className={`overflow-hidden transition-all duration-300 ${
                isOpen ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
              }`}
            >
              <div className="px-4 py-3.5 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-800/50">
                {item.content}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
