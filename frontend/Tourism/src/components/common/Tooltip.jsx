import { useState, useRef, useEffect } from "react"

/**
 * Accessible tooltip with positioning, delay, and keyboard support.
 */
export default function Tooltip({ content, children, position = "top", delay = 300, className = "" }) {
  const [visible, setVisible] = useState(false)
  const timeoutRef = useRef(null)
  const containerRef = useRef(null)

  const show = () => {
    timeoutRef.current = setTimeout(() => setVisible(true), delay)
  }

  const hide = () => {
    clearTimeout(timeoutRef.current)
    setVisible(false)
  }

  useEffect(() => () => clearTimeout(timeoutRef.current), [])

  const positions = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  }

  const arrows = {
    top: "top-full left-1/2 -translate-x-1/2 border-t-gray-900 dark:border-t-slate-700 border-x-transparent border-b-transparent",
    bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-gray-900 dark:border-b-slate-700 border-x-transparent border-t-transparent",
    left: "left-full top-1/2 -translate-y-1/2 border-l-gray-900 dark:border-l-slate-700 border-y-transparent border-r-transparent",
    right: "right-full top-1/2 -translate-y-1/2 border-r-gray-900 dark:border-r-slate-700 border-y-transparent border-l-transparent",
  }

  return (
    <div
      ref={containerRef}
      className={`relative inline-block ${className}`}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className={`absolute z-[80] px-3 py-1.5 text-xs font-medium text-white bg-gray-900 dark:bg-slate-700 rounded-lg shadow-lg whitespace-nowrap pointer-events-none ${positions[position] || positions.top}`}
        >
          {content}
          <div className={`absolute w-0 h-0 border-4 ${arrows[position] || arrows.top}`} />
        </div>
      )}
    </div>
  )
}
