const Filter = ({ label, options, value, onChange }) => (
  <div className="flex flex-col gap-1">
    {label && <label className="text-xs font-medium text-gray-500">{label}</label>}
    <select
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

export default Filter