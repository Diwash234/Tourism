import { useState, useMemo, useCallback } from "react"
import { FiChevronUp, FiChevronDown, FiSearch, FiFilter, FiDownload, FiRefreshCw } from "react-icons/fi"

/**
 * Advanced data table with sorting, filtering, pagination,
 * row selection, and export functionality.
 */
export default function DataTable({
  columns = [],
  data = [],
  pageSize = 10,
  searchable = true,
  sortable = true,
  selectable = false,
  onRowClick,
  onSelectionChange,
  onExport,
  emptyMessage = "No data available",
  loading = false,
}) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState("asc")
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState(new Set())
  const [filters, setFilters] = useState({})

  // Filter and search data
  const filteredData = useMemo(() => {
    let result = [...data]

    // Apply search
    if (search && searchable) {
      const q = search.toLowerCase()
      result = result.filter(row =>
        columns.some(col => {
          const val = typeof col.accessor === "function" ? col.accessor(row) : row[col.accessor]
          return String(val || "").toLowerCase().includes(q)
        })
      )
    }

    // Apply column filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        result = result.filter(row => {
          const col = columns.find(c => c.key === key)
          if (!col) return true
          const val = typeof col.accessor === "function" ? col.accessor(row) : row[key]
          return String(val || "").toLowerCase().includes(String(value).toLowerCase())
        })
      }
    })

    // Apply sorting
    if (sortKey && sortable) {
      const col = columns.find(c => c.key === sortKey)
      result.sort((a, b) => {
        const aVal = typeof col.accessor === "function" ? col.accessor(a) : a[sortKey]
        const bVal = typeof col.accessor === "function" ? col.accessor(b) : b[sortKey]
        if (aVal < bVal) return sortDir === "asc" ? -1 : 1
        if (aVal > bVal) return sortDir === "asc" ? 1 : -1
        return 0
      })
    }

    return result
  }, [data, search, filters, sortKey, sortDir, columns, searchable, sortable])

  // Paginate data
  const totalPages = Math.ceil(filteredData.length / pageSize)
  const paginatedData = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredData.slice(start, start + pageSize)
  }, [filteredData, page, pageSize])

  const handleSort = useCallback((key) => {
    if (sortKey === key) {
      setSortDir(d => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }, [sortKey])

  const handleSelectAll = useCallback(() => {
    if (selected.size === paginatedData.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(paginatedData.map(r => r.id)))
    }
  }, [selected.size, paginatedData])

  const handleSelectRow = useCallback((id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  useEffect(() => {
    onSelectionChange?.(Array.from(selected))
  }, [selected, onSelectionChange])

  const handleExportCSV = useCallback(() => {
    const headers = columns.map(c => c.label).join(",")
    const rows = filteredData.map(row =>
      columns.map(c => {
        const val = typeof c.accessor === "function" ? c.accessor(row) : row[c.accessor]
        return `"${String(val || "").replace(/"/g, '""')}"`
      }).join(",")
    )
    const csv = [headers, ...rows].join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "export.csv"
    a.click()
    URL.revokeObjectURL(url)
  }, [filteredData, columns])

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden">
      {/* Toolbar */}
      {(searchable || onExport) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 border-b border-[var(--ny-border)]">
          <div className="flex items-center gap-2">
            {searchable && (
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                  placeholder="Search..."
                  className="text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 w-64 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {onExport && (
              <button
                type="button"
                onClick={handleExportCSV}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
              >
                <FiDownload size={14} />
                Export
              </button>
            )}
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
                    checked={selected.size === paginatedData.length && paginatedData.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300"
                    aria-label="Select all rows"
                  />
                </th>
              )}
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => sortable && handleSort(col.key)}
                  className={`px-4 py-3 text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 ${sortable ? "cursor-pointer hover:text-gray-700 dark:hover:text-gray-200" : ""}`}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortable && sortKey === col.key && (
                      sortDir === "asc" ? <FiChevronUp size={12} /> : <FiChevronDown size={12} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--ny-border)]">
            {loading ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-4 py-8 text-center">
                  <LoadingSpinner size="md" label="Loading data..." />
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-4 py-8 text-center">
                  <EmptyState message={emptyMessage} />
                </td>
              </tr>
            ) : (
              paginatedData.map((row, i) => (
                <tr
                  key={row.id || i}
                  onClick={() => onRowClick?.(row)}
                  className={`transition-colors hover:bg-gray-50 dark:hover:bg-slate-700/50 ${onRowClick ? "cursor-pointer" : ""}`}
                >
                  {selectable && (
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(row.id)}
                        onChange={() => handleSelectRow(row.id)}
                        className="rounded border-gray-300"
                        aria-label="Select row"
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                      {col.render ? col.render(row) : row[col.accessor]}
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
            Page {page} of {totalPages}
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
