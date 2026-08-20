import { useEffect, useMemo, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import { FiSearch, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"

const ROUTES = {
  destination: () => "/admin?section=places",
  user: () => "/admin?section=users",
  hotel: () => "/admin?section=hotel_bookings",
  feedback: () => "/admin?section=feedback_workspace",
  alert: () => "/admin?section=safety_management",
  page: () => "/admin?section=cms",
  section: () => "/admin?section=cms",
  navigation: () => "/admin?section=cms",
  image: () => "/admin?section=media_library",
  restaurant: () => "/admin?section=travel_services",
  review: () => "/admin?section=review_moderation",
}
const FILTERS = ["", "destination", "page", "section", "image", "hotel", "user", "alert", "feedback", "navigation", "restaurant", "review"]

export default function AdminGlobalSearch() {
  const navigate = useNavigate()
  const box = useRef(null)
  const [q, setQ] = useState("")
  const [type, setType] = useState("")
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [error, setError] = useState("")
  const [active, setActive] = useState(0)

  useEffect(() => {
    if (q.trim().length < 2) {
      setRows([])
      setOpen(false)
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      setError("")
      try {
        const { data } = await adminApi.globalSearch(q.trim(), type ? { type } : {})
        setRows(data.results || [])
        setActive(0)
        setOpen(true)
      } catch (e) {
        setRows([])
        setOpen(true)
        setError(e.response?.data?.detail || "Search failed")
      } finally {
        setLoading(false)
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [q, type])

  useEffect(() => {
    const close = (event) => {
      if (!box.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener("mousedown", close)
    return () => document.removeEventListener("mousedown", close)
  }, [])

  const grouped = useMemo(
    () => rows.reduce((all, row) => ({ ...all, [row.type]: [...(all[row.type] || []), row] }), {}),
    [rows]
  )

  const choose = (row) => {
    if (!row) return
    setOpen(false)
    setQ("")
    navigate((ROUTES[row.type] || (() => "/admin"))(row))
  }

  const onKeyDown = (event) => {
    if (!open || !rows.length) return
    if (event.key === "ArrowDown") {
      event.preventDefault()
      setActive((value) => (value + 1) % rows.length)
    }
    if (event.key === "ArrowUp") {
      event.preventDefault()
      setActive((value) => (value - 1 + rows.length) % rows.length)
    }
    if (event.key === "Enter") {
      event.preventDefault()
      choose(rows[active])
    }
    if (event.key === "Escape") setOpen(false)
  }

  return (
    <div ref={box} className="relative max-w-xl flex-1">
      <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
      <input
        value={q}
        onFocus={() => rows.length && setOpen(true)}
        onChange={(event) => setQ(event.target.value)}
        onKeyDown={onKeyDown}
        className="w-full rounded-xl border border-slate-700 bg-slate-900 py-2 pl-10 pr-10 text-sm text-white"
        placeholder="Search destinations, pages, images, hotels, users…"
        aria-label="Admin global search"
      />
      {q && (
        <button onClick={() => { setQ(""); setRows([]) }} className="absolute right-3 top-2.5 text-slate-500" aria-label="Clear search">
          <FiX />
        </button>
      )}
      {open && (
        <div className="absolute left-0 right-0 z-[80] mt-2 max-h-[28rem] overflow-y-auto rounded-2xl border border-slate-700 bg-slate-950 p-2 shadow-2xl">
          <div className="mb-2 flex flex-wrap gap-1 px-2">
            {FILTERS.map((item) => (
              <button
                key={item || "all"}
                onClick={() => setType(item)}
                className={`rounded-full px-2 py-1 text-[10px] font-black uppercase ${type === item ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}
              >
                {item || "all"}
              </button>
            ))}
          </div>
          {loading && <p className="p-4 text-sm text-slate-400">Searching permitted modules…</p>}
          {error && <p className="p-4 text-sm text-rose-400">{error}</p>}
          {!loading && !error && !rows.length && <p className="p-4 text-sm text-slate-500">No permitted records found.</p>}
          {Object.entries(grouped).map(([group, items]) => (
            <section key={group}>
              <h3 className="px-3 pb-1 pt-3 text-[10px] font-black uppercase tracking-widest text-amber-400">{group}</h3>
              {items.map((row) => {
                const index = rows.indexOf(row)
                return (
                  <button
                    key={`${group}-${row.id}`}
                    onClick={() => choose(row)}
                    className={`w-full rounded-lg px-3 py-2 text-left text-sm ${index === active ? "bg-slate-800 text-white" : "text-slate-200 hover:bg-slate-800"}`}
                  >
                    <span className="block truncate">{row.label}</span>
                    {row.snippet && <span className="block truncate text-[11px] text-slate-400">{row.snippet}</span>}
                    <span className="text-[10px] uppercase text-slate-500">{row.module} · #{row.id}</span>
                  </button>
                )
              })}
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
