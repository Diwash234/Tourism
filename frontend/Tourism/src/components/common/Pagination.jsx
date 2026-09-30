import { useEffect, useState } from "react"
import { FiChevronLeft, FiChevronRight, FiMoreHorizontal } from "react-icons/fi"

export default function Pagination({ page, totalPages, onPageChange, pageSize, onPageSizeChange, totalItems }) {
  const [jumpValue, setJumpValue] = useState(String(page || 1))
  useEffect(() => { setJumpValue(String(page || 1)) }, [page])
  const currentPage = Math.min(Math.max(Number(page) || 1, 1), Math.max(Number(totalPages) || 1, 1))
  const safeTotalPages = Math.max(Number(totalPages) || 1, 1)
  const getPageNumbers = () => {
    if (safeTotalPages <= 7) return Array.from({ length: safeTotalPages }, (_, index) => index + 1)
    const pages = [1]
    const left = Math.max(2, currentPage - 1)
    const right = Math.min(safeTotalPages - 1, currentPage + 1)
    if (left > 2) pages.push("...")
    for (let number = left; number <= right; number += 1) pages.push(number)
    if (right < safeTotalPages - 1) pages.push("...")
    pages.push(safeTotalPages)
    return pages
  }
  const jumpToPage = (event) => {
    event.preventDefault()
    const value = jumpValue.trim()
    if (!/^\\d+$/.test(value)) return
    const requested = Number(value)
    if (requested < 1 || requested > safeTotalPages) { setJumpValue(String(currentPage)); return }
    onPageChange(requested)
  }
  if (safeTotalPages <= 1 && !onPageSizeChange) return null
  const firstItem = totalItems ? (currentPage - 1) * pageSize + 1 : 0
  const lastItem = totalItems ? Math.min(currentPage * pageSize, totalItems) : 0
  return (
    <nav className="flex flex-col gap-4 border-t border-[var(--ny-border)] py-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Pagination">
      <div className="flex flex-wrap items-center gap-2 text-sm text-[var(--ny-text-secondary)]">
        {totalItems != null && <span>Showing {firstItem}–{lastItem} of {totalItems}</span>}
        {onPageSizeChange && <label className="flex items-center gap-2"><span className="sr-only">Results per page</span><select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))} className="min-h-9 rounded-lg border border-[var(--ny-border)] bg-[var(--ny-white)] px-2 text-sm" aria-label="Results per page">{[10, 20, 50, 100].map((size) => <option key={size} value={size}>{size} / page</option>)}</select></label>}
      </div>
      <div className="flex flex-wrap items-center justify-end gap-1.5">
        <button type="button" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage <= 1} className="ny-btn ny-btn-secondary ny-btn-sm" aria-label="Previous page"><FiChevronLeft size={15} aria-hidden="true" /><span className="hidden sm:inline">Previous</span></button>
        <div className="hidden items-center gap-1 sm:flex">{getPageNumbers().map((number, index) => number === "..." ? <span key={"ellipsis-" + index} className="grid h-9 w-8 place-items-center text-[var(--ny-text-muted)]" aria-hidden="true"><FiMoreHorizontal size={15} /></span> : <button key={number} type="button" onClick={() => onPageChange(number)} aria-current={number === currentPage ? "page" : undefined} className={number === currentPage ? "grid h-9 min-w-9 place-items-center rounded-lg bg-[var(--ny-green)] px-2 text-sm font-bold text-white" : "grid h-9 min-w-9 place-items-center rounded-lg border border-[var(--ny-border)] bg-[var(--ny-white)] px-2 text-sm font-semibold text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)]"}>{number}</button>)}</div>
        <span className="px-2 text-xs font-semibold text-[var(--ny-text-secondary)] sm:hidden">Page {currentPage} of {safeTotalPages}</span>
        <form onSubmit={jumpToPage} className="hidden items-center gap-1.5 md:flex" aria-label="Jump to page"><label htmlFor="pagination-jump" className="sr-only">Jump to page</label><input id="pagination-jump" value={jumpValue} onChange={(event) => setJumpValue(event.target.value)} inputMode="numeric" pattern="\\d+" placeholder="Jump to…" aria-label="Jump to page number" className="h-9 w-24 rounded-lg border border-[var(--ny-border)] bg-[var(--ny-white)] px-2 text-center text-sm" /><button type="submit" className="ny-btn ny-btn-secondary ny-btn-sm">Go</button></form>
        <span className="hidden px-2 text-xs font-semibold text-[var(--ny-text-secondary)] lg:inline">Page {currentPage} of {safeTotalPages}</span>
        <button type="button" onClick={() => onPageChange(currentPage + 1)} disabled={currentPage >= safeTotalPages} className="ny-btn ny-btn-secondary ny-btn-sm" aria-label="Next page"><span className="hidden sm:inline">Next</span><FiChevronRight size={15} aria-hidden="true" /></button>
      </div>
    </nav>
  )
}