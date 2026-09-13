import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { FiSearch } from "react-icons/fi"
import adminApi from "../../api/adminApi"

const TYPE_ICON = {
  destination: "📍", hotel: "🏨", user: "👤", feedback: "💬", alert: "⚠️",
  page: "📄", section: "📑", navigation: "🧭", image: "🖼️", restaurant: "🍽️",
  review: "⭐", listing: "🛍️", partner: "🤝",
}

/**
 * Permission-respecting global search (Staff Ops spec §22).
 * The backend (/admin/search/) already filters results by the caller's
 * capabilities per module — this is the staff-facing UI for it.
 */
export default function StaffGlobalSearch() {
  const navigate = useNavigate()
  const [q, setQ] = useState("")
  const [results, setResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const boxRef = useRef(null)

  useEffect(() => {
    if (q.trim().length < 2) return
    const t = setTimeout(() => {
      setSearching(true)
      adminApi.globalSearch(q.trim())
        .then(({ data }) => setResults(data))
        .catch(() => setResults({ results: [], count: 0 }))
        .finally(() => setSearching(false))
    }, 350)
    return () => clearTimeout(t)
  }, [q])

  useEffect(() => {
    const onClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setResults(null)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [])

  const goto = (r) => {
    setResults(null)
    setQ("")
    const known = ["destinations", "images", "hotels", "restaurants", "reviews", "feedback", "safety", "content", "marketplace", "users"]
    navigate(known.includes(r.module) ? `/staff/${r.module}` : "/staff")
  }

  return (
    <div ref={boxRef} className="relative w-full sm:w-80">
      <div className="flex items-center gap-2 bg-white border rounded-xl px-3 py-2">
        <FiSearch className={searching ? "animate-pulse text-slate-400" : "text-slate-400"} />
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            if (e.target.value.trim().length < 2) setResults(null)
          }}
          placeholder="Search everything you can access…"
          aria-label="Global search (results limited to your permissions)"
          className="w-full text-sm focus:outline-none"
        />
      </div>
      {results && (
        <div className="absolute z-40 mt-1 w-full bg-white border rounded-xl shadow-lg max-h-80 overflow-y-auto">
          {results.results.map((r) => (
            <button key={`${r.type}-${r.id}`} onClick={() => goto(r)} className="w-full text-left px-3 py-2 hover:bg-slate-50 border-b last:border-0">
              <p className="text-sm text-slate-800 font-bold truncate">{TYPE_ICON[r.type] || "🔎"} {r.label}</p>
              {r.snippet && <p className="text-xs text-slate-500 truncate">{r.snippet}</p>}
            </button>
          ))}
          {!results.results.length && (
            <p className="p-4 text-center text-xs text-slate-400">
              {q.trim().length < 2 ? "Type at least 2 characters" : "No results inside your permission scope."}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
