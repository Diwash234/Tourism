import { useState, useMemo } from "react"
import { FiChevronUp, FiChevronDown, FiSearch, FiFilter } from "react-icons/fi"

/**
 * Reusable data table with sorting, filtering, pagination,
 * and row selection.
 */
export default function DataTable({
  columns = [],
  data = [],
  pageSize = 10,
  searchable = true,
  selectable = false,
  onRowClick,
  className = "",
}) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState("asc")
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState(new Set())

  const filtered = useMemo(() => {
    if (!search) return data
    const q = search.toLowerCase()
    return data.filter(row =>
      columns.some(col => {
        const val = typeof col.accessor === "function" ? col.accessor(row) : row[col.accessor]
        return String(val || "").toLowerCase().includes(q)
      })
    )
  }, [data, search, columns])

  const sorted = useMemo(() => {
    if (!sortKey) return filtered
    return [...filtered].sort((a, b) => {
      const col = columns.find(c => c.key === sortKey)
      const aVal = typeof col?.accessor === "function" ? col.accessor(a) : a[sortKey]
      const bVal = typeof col?.accessor === "function" ? col.accessor(b) : b[sortKey]
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1
      return 0
    })
  }, [filtered, sortKey, sortDir, columns])

  const totalPages = Math.ceil(sorted.length / pageSize)
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize)

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selected.size === paged.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(paged.map(r => r.id)))
    }
  }

  return (
    <div className={`bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden ${className}`}>
      {/* Search Bar */}
      {searchable && (
        <div className="px-4 py-3 border-b border-[var(--ny-border)]">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="search"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              placeholder="Search..."
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--ny-border)] bg-gray-50 dark:bg-slate-800/50">
              {selectable && (
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selected.size === paged.length && paged.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300"
                    aria-label="Select all"
                  />
                </th>
              )}
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 ${col.sortable !== false ? "cursor-pointer hover:text-gray-700" : ""}`}
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
            {paged.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-4 py-8 text-center text-sm text-gray-400">
                  No data available
                </td>
              </tr>
            ) : (
              paged.map((row, i) => (
                <tr
                  key={row.id || i}
                  onClick={() => onRowClick?.(row)}
                  className={`transition-colors ${onRowClick ? "cursor-pointer" : ""} hover:bg-gray-50 dark:hover:bg-slate-700/50`}
                >
                  {selectable && (
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(row.id)}
                        onChange={() => toggleSelect(row.id)}
                        className="rounded border-gray-300"
                        aria-label="Select row"
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                      {col.render ? col.render(row) : (
                        typeof col.accessor === "function" ? col.accessor(row) : row[col.accessor]
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--ny-border)]">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, sorted.length)} of {sorted.length}
          </p>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
              let pageNum
              if (totalPages <= 5) pageNum = i + 1
              else if (page <= 3) pageNum = i + 1
              else if (page >= totalPages - 2) pageNum = totalPages - 4 + i
              else pageNum = page - 2 + i
              return (
                <button
                  key={pageNum}
                  type="button"
                  onClick={() => setPage(pageNum)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                    pageNum === page
                      ? "bg-[var(--ny-green)] text-white"
                      : "border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700"
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
            <button
              type="button"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
