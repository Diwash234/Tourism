import { useState, useRef, useEffect } from "react"
import { FiChevronDown, FiX, FiCheck } from "react-icons/fi"

/**
 * Multi-select dropdown with search, select all, and clear all.
 */
export default function MultiSelect({ options = [], value = [], onChange, placeholder = "Select...", className = "" }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const box = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onDown = (e) => {
      if (!box.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [open])

  const filtered = options.filter(opt =>
    opt.label.toLowerCase().includes(search.toLowerCase())
  )

  const toggle = (val) => {
    const newValue = value.includes(val)
      ? value.filter(v => v !== val)
      : [...value, val]
    onChange?.(newValue)
  }

  const selectAll = () => onChange?.(options.map(o => o.value))
  const clearAll = () => onChange?.([])

  return (
    <div ref={box} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center justify-between px-3 py-2.5 text-sm rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="truncate">
          {value.length === 0
            ? placeholder
            : value.length === options.length
            ? "All selected"
            : `${value.length} selected`}
        </span>
        <FiChevronDown size={16} className={`text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl overflow-hidden">
          <div className="p-2 border-b border-gray-100 dark:border-slate-700">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full text-sm rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 px-3 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-100 dark:border-slate-700">
            <button type="button" onClick={selectAll} className="text-xs text-[var(--ny-green)] hover:underline font-medium">
              Select all
            </button>
            <button type="button" onClick={clearAll} className="text-xs text-red-500 hover:underline font-medium">
              Clear all
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto" role="listbox" aria-multiselectable="true">
            {filtered.length === 0 ? (
              <p className="px-3 py-2 text-xs text-gray-400">No options found</p>
            ) : (
              filtered.map((opt) => {
                const selected = value.includes(opt.value)
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggle(opt.value)}
                    className={`flex w-full items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                      selected
                        ? "bg-[var(--ny-soft-green)] text-[var(--ny-green)]"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                    }`}
                    role="option"
                    aria-selected={selected}
                  >
                    <span className={`flex h-4 w-4 items-center justify-center rounded border ${
                      selected
                        ? "bg-[var(--ny-green)] border-[var(--ny-green)] text-white"
                        : "border-gray-300 dark:border-slate-600"
                    }`}>
                      {selected && <FiCheck size={10} />}
                    </span>
                    {opt.label}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
