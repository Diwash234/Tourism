import { useState, useMemo } from "react"
import { FiChevronUp, FiChevronDown, FiSearch, FiFilter, FiDownload } from "react-icons/fi"

/**
 * Reusable data table with sorting, filtering, pagination,
 * and CSV export. Works with any array of objects.
 */
export default function DataTable({
  columns = [],
  data = [],
  pageSize = 10,
  searchable = true,
  exportable = true,
  onRowClick,
  emptyMessage = "No data available",
}) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState("asc")
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [filters, setFilters] = useState({})

  // Filter and search data
  const processedData = useMemo(() => {
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
              const val = typeof columns.find(c => c.key === key)?.accessor === "function"
                ? columns.find(c => c.key === key).accessor(row)
                : row[key]
              return String(val || "").toLowerCase().includes(String(value).toLowerCase())
            })
      }
    })

    // Apply sorting
    if (sortKey) {
      const col = columns.find(c => c.key === sortKey)
      if (col) {
        result.sort((a, b) => {
          const aVal = typeof col.accessor === "function" ? col.accessor(a) : a[sortKey]
          const bVal = typeof col.accessor === "function" ? col.accessor(b) : b[sortKey]
          if (aVal < bVal) return sortDir === "asc" ? -1 : 1
          if (aVal > bVal) return sortDir === "asc" ? 1 : -1
          return 0
        })
      }
    }

    return result
  }, [data, search, filters, sortKey, sortDir, columns, searchable])

  // Paginate
  const totalPages = Math.ceil(processedData.length / pageSize)
  const paginatedData = processedData.slice((page - 1) * pageSize, page * pageSize)

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const handleExport = () => {
    const headers = columns.map(c => c.label).join(",")
    const rows = processedData.map(row =>
      columns.map(col => {
        const val = typeof col.accessor === "function" ? col.accessor(row) : row[col.accessor]
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
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden">
      {/* Toolbar */}
      {(searchable || exportable) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 border-b border-[var(--ny-border)]">
          {searchable && (
            <div className="relative w-full sm:w-64">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="search"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                placeholder="Search..."
                className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          )}
          {exportable && (
            <button
              type="button"
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              <FiDownload size={14} />
              Export CSV
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--ny-border)] bg-gray-50 dark:bg-slate-800/50">
                {columns.map(col => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
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
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, i) => (
                <tr
                  key={row.id || i}
                  onClick={() => onRowClick?.(row)}
                  className={`transition-colors ${onRowClick ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-700/50" : ""}`}
                >
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                      {col.render ? col.render(row) : typeof col.accessor === "function" ? col.accessor(row) : row[col.accessor]}
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
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, processedData.length)} of {processedData.length}
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
