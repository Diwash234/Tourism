import { useMemo, useState } from "react"
import { FiSearch, FiChevronDown } from "react-icons/fi"

// A small, dependency-free searchable combobox. Typing filters the loaded
// options and picking one stores its id — replaces "type a raw numeric ID"
// inputs so admins cannot submit nonexistent hotels/users.
export default function SearchSelect({ label, options, value, onChange, placeholder, required = false }) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)

  const selected = options.find((o) => String(o.id) === String(value))
  const filtered = useMemo(() => {
    const q = (query || "").toLowerCase()
    const base = selected && !query ? [selected] : options
    return base.filter((o) => String(o.label).toLowerCase().includes(q)).slice(0, 8)
  }, [options, query, selected])

  return (
    <div className="relative">
      {label && <label className="text-xs font-medium text-gray-500">{label}</label>}
      <div className="relative mt-1">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
        <input
          className="input-field pl-9 pr-8"
          value={open ? query : selected ? selected.label : query}
          placeholder={placeholder}
          required={required && !selected}
          onFocus={() => { setOpen(true); setQuery("") }}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); if (value) onChange("") }}
        />
        <FiChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
      </div>
      {open && (
        <ul className="absolute z-20 mt-1 w-full max-h-56 overflow-auto rounded-xl border border-gray-200 bg-white shadow-lg">
          {filtered.length === 0 && <li className="px-3 py-2 text-xs text-gray-400">No matches</li>}
          {filtered.map((o) => (
            <li key={o.id}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => { onChange(o.id); setOpen(false); setQuery("") }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-emerald-50 truncate"
              >
                {o.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
