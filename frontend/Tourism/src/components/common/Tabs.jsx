import { useState, useRef, useEffect } from "react"

/**
 * Accessible tabs component with keyboard navigation (arrow keys, Home, End).
 * Supports horizontal and vertical orientations.
 */
export default function Tabs({ tabs, defaultIndex = 0, orientation = "horizontal", className = "", onChange }) {
  const [active, setActive] = useState(defaultIndex)
  const tabRefs = useRef([])

  useEffect(() => {
    tabRefs.current = tabRefs.current.slice(0, tabs.length)
  }, [tabs.length])

  const handleKeyDown = (e, index) => {
    let newIndex = null
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault()
      newIndex = (index + 1) % tabs.length
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault()
      newIndex = (index - 1 + tabs.length) % tabs.length
    } else if (e.key === "Home") {
      e.preventDefault()
      newIndex = 0
    } else if (e.key === "End") {
      e.preventDefault()
      newIndex = tabs.length - 1
    }
    if (newIndex !== null) {
      setActive(newIndex)
      onChange?.(newIndex)
      tabRefs.current[newIndex]?.focus()
    }
  }

  const handleClick = (index) => {
    setActive(index)
    onChange?.(index)
  }

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-orientation={orientation}
        className={`flex ${orientation === "vertical" ? "flex-col gap-1" : "gap-1 border-b border-[var(--ny-border)]"}`}
      >
        {tabs.map((tab, i) => (
          <button
            key={i}
            ref={el => tabRefs.current[i] = el}
            role="tab"
            aria-selected={active === i}
            aria-controls={`tabpanel-${i}`}
            id={`tab-${i}`}
            tabIndex={active === i ? 0 : -1}
            onClick={() => handleClick(i)}
            onKeyDown={e => handleKeyDown(e, i)}
            className={`px-4 py-2.5 text-sm font-semibold rounded-t-lg transition-all whitespace-nowrap ${
              active === i
                ? "bg-[var(--ny-soft-green)] text-[var(--ny-green)] border-b-2 border-[var(--ny-green)]"
                : "text-[var(--ny-text-secondary)] hover:text-[var(--ny-text)] hover:bg-gray-50 dark:hover:bg-slate-800"
            }`}
          >
            {tab.icon && <span className="mr-2 inline-flex align-middle">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div
          key={i}
          role="tabpanel"
          id={`tabpanel-${i}`}
          aria-labelledby={`tab-${i}`}
          hidden={active !== i}
          className="pt-4"
        >
          {active === i && tab.content}
        </div>
      ))}
    </div>
  )
}
