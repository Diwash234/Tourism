import { useId } from "react"

// The label is linked to the select so screen readers announce what it filters.
// Without a visible label, `ariaLabel` (or the generic "Filter") names it.
const Filter = ({ label, ariaLabel, options, value, onChange }) => {
  const id = useId()
  return (
    <div className="flex flex-col gap-1">
      {label && <label htmlFor={id} className="text-xs font-medium text-gray-500">{label}</label>}
      <select
        id={id}
        aria-label={label ? undefined : ariaLabel || "Filter"}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        className="input-field cursor-pointer"
      >
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default Filter
