import { useState, useRef, useEffect } from "react"
import { FiCheck } from "react-icons/fi"

const PRESET_COLORS = [
  "#075B48", "#087F63", "#63E6BE", "#F5B51B", "#E9A915",
  "#C62828", "#2563A6", "#7C3AED", "#DB2777", "#059669",
  "#D97706", "#4F46E5", "#0891B2", "#65A30D", "#9333EA",
]

/**
 * Color picker with preset colors and custom hex input.
 */
export default function ColorPicker({ value, onChange, className = "" }) {
  const [open, setOpen] = useState(false)
  const [customColor, setCustomColor] = useState(value || PRESET_COLORS[0])
  const box = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onDown = (e) => {
      if (!box.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [open])

  const handleColorSelect = (color) => {
    onChange?.(color)
    setCustomColor(color)
  }

  return (
    <div ref={box} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        aria-haspopup="dialog"
        aria-expanded={open}
      >
        <span className="h-5 w-5 rounded-md border border-gray-200 dark:border-slate-600" style={{ backgroundColor: value || customColor }} />
        <span className="font-medium">{value || customColor}</span>
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-56 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl p-3" role="dialog" aria-label="Color picker">
          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">Preset Colors</p>
          <div className="grid grid-cols-5 gap-2 mb-3">
            {PRESET_COLORS.map(color => (
              <button
                key={color}
                type="button"
                onClick={() => handleColorSelect(color)}
                className="h-8 w-8 rounded-lg border border-gray-200 dark:border-slate-600 flex items-center justify-center transition-transform hover:scale-110"
                style={{ backgroundColor: color }}
                aria-label={`Select color ${color}`}
              >
                {value === color && <FiCheck size={14} className="text-white" />}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500 dark:text-gray-400">Custom:</label>
            <input
              type="color"
              value={customColor}
              onChange={(e) => { setCustomColor(e.target.value); onChange?.(e.target.value) }}
              className="h-8 w-8 rounded-lg border border-gray-200 dark:border-slate-600 cursor-pointer"
            />
            <input
              type="text"
              value={customColor}
              onChange={(e) => { setCustomColor(e.target.value); onChange?.(e.target.value) }}
              className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              placeholder="#000000"
            />
          </div>
        </div>
      )}
    </div>
  )
}
