import { useState } from "react"
import { FiChevronUp, FiChevronDown } from "react-icons/fi"

/**
 * Responsive table that transforms into cards on mobile.
 * Supports sorting, row actions, and empty state.
 */
export default function ResponsiveTable({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyMessage = "No data available",
  className = "",
}) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState("asc")

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const sortedData = [...data].sort((a, b) => {
    if (!sortKey) return 0
    const aVal = a[sortKey]
    const bVal = b[sortKey]
    if (aVal < bVal) return sortDir === "asc" ? -1 : 1
    if (aVal > bVal) return sortDir === "asc" ? 1 : -1
    return 0
  })

  return (
    <div className={`overflow-hidden ${className}`}>
      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--ny-border)] bg-gray-50 dark:bg-slate-800/50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 ${
                    col.sortable !== false ? "cursor-pointer hover:text-gray-700 dark:hover:text-gray-200" : ""
                  }`}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && (
                      sortDir === "asc" ? <FiChevronUp size={12} /> : <FiChevronDown size={12} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--ny-border)]">
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sortedData.map((row, i) => (
                <tr
                  key={keyExtractor ? keyExtractor(row) : i}
                  onClick={() => onRowClick?.(row)}
                  className={`transition-colors ${onRowClick ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50" : ""}`}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {sortedData.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-8">{emptyMessage}</p>
        ) : (
          sortedData.map((row, i) => (
            <div
              key={keyExtractor ? keyExtractor(row) : i}
              onClick={() => onRowClick?.(row)}
              className={`bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 ${
                onRowClick ? "cursor-pointer" : ""
              }`}
            >
              {columns.map((col) => (
                <div key={col.key} className="flex justify-between py-1.5">
                  <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">{col.label}</span>
                  <span className="text-sm text-gray-700 dark:text-gray-300 text-right">
                    {col.render ? col.render(row) : row[col.key]}
                  </span>
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
