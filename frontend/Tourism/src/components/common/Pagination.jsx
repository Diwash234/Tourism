import { useState } from "react"
import { FiChevronLeft, FiChevronRight } from "react-icons/fi"

// Builds a windowed page list like [1, "…", 8, 9, 10, "…", 42] so a catalog
// with hundreds of pages never renders hundreds of buttons (audit REQ-028).
const buildWindow = (current, total) => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = new Set([1, total, current, current - 1, current + 1])
  if (current <= 4) [2, 3, 4, 5].forEach((p) => pages.add(p))
  if (current >= total - 3) [total - 4, total - 3, total - 2, total - 1].forEach((p) => pages.add(p))
  const sorted = [...pages].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b)
  const out = []
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) out.push("…")
    out.push(p)
  })
  return out
}

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  const [jump, setJump] = useState("")
  const [jumpError, setJumpError] = useState("")
  if (totalPages <= 1) return null

  const go = (p) => {
    if (p >= 1 && p <= totalPages && p !== currentPage) onPageChange(p)
  }

  const submitJump = (e) => {
    e.preventDefault()
    const raw = jump.trim()
    if (!/^\d+$/.test(raw)) {
      setJumpError("Enter a page number (digits only).")
      return
    }
    const n = parseInt(raw, 10)
    if (n < 1 || n > totalPages) {
      setJumpError(`Page must be between 1 and ${totalPages}.`)
      return
    }
    setJumpError("")
    setJump("")
    go(n)
  }

  const btnBase =
    "h-9 min-w-9 px-2 rounded-lg text-sm font-medium border transition-colors"

  return (
    <div className="flex flex-col items-center gap-3 mt-8">
      <div className="flex items-center justify-center gap-1.5 flex-wrap">
        <button
          onClick={() => go(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Previous page"
          className={`${btnBase} border-gray-200 p-2 disabled:opacity-40`}
        >
          <FiChevronLeft />
        </button>
        {buildWindow(currentPage, totalPages).map((page, i) =>
          page === "…" ? (
            <span key={`gap-${i}`} className="px-1 text-gray-400 select-none" aria-hidden="true">
              …
            </span>
          ) : (
            <button
              key={page}
              onClick={() => go(page)}
              aria-label={`Page ${page}`}
              aria-current={page === currentPage ? "page" : undefined}
              className={
                page === currentPage
                  ? `${btnBase} bg-primary-500 text-white border-primary-500`
                  : `${btnBase} border-gray-200 text-gray-600 hover:bg-gray-50`
              }
            >
              {page}
            </button>
          )
        )}
        <button
          onClick={() => go(currentPage + 1)}
          disabled={currentPage === totalPages}
          aria-label="Next page"
          className={`${btnBase} border-gray-200 p-2 disabled:opacity-40`}
        >
          <FiChevronRight />
        </button>
      </div>

      <form onSubmit={submitJump} className="flex items-center gap-2 text-sm text-gray-600">
        <span aria-live="polite">
          Page {currentPage} of {totalPages}
        </span>
        <label className="flex items-center gap-1.5">
          <span className="sr-only">Go to page number</span>
          <input
            type="text"
            inputMode="numeric"
            value={jump}
            onChange={(e) => {
              setJump(e.target.value)
              if (jumpError) setJumpError("")
            }}
            placeholder="Jump to…"
            className="h-9 w-24 rounded-lg border border-gray-200 px-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-300"
          />
        </label>
        <button
          type="submit"
          className="h-9 px-3 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600"
        >
          Go
        </button>
        {jumpError && (
          <span role="alert" className="text-red-600 text-xs">
            {jumpError}
          </span>
        )}
      </form>
    </div>
  )
}

export default Pagination
