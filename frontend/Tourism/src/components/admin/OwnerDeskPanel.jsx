import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  FiAlertTriangle, FiCheck, FiImage, FiMapPin, FiMessageSquare, FiPlus, FiRefreshCw, FiStar, FiTrash2, FiX,
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const KINDS = [
  ["festival", "Festival"],
  ["closure", "Trail / site closure"],
  ["permit", "Permit / entry"],
  ["seasonal", "Seasonal advice"],
  ["crowd", "Crowd / wait"],
  ["transport", "Transport"],
  ["info", "General notice"],
]

const emptyNotice = {
  title: "",
  kind: "info",
  body: "",
  city: "",
  district: "",
  destination_id: "",
  starts_at: "",
  ends_at: "",
  is_published: true,
}

const toLocalInput = (value) => {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  const pad = (n) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const kindTone = {
  festival: "bg-amber-100 text-amber-900",
  closure: "bg-rose-100 text-rose-800",
  permit: "bg-sky-100 text-sky-800",
  seasonal: "bg-emerald-100 text-emerald-800",
  crowd: "bg-orange-100 text-orange-800",
  transport: "bg-indigo-100 text-indigo-800",
  info: "bg-slate-100 text-slate-700",
}

export default function OwnerDeskPanel() {
  const { showToast } = useToast()
  const [desk, setDesk] = useState({ queue: {}, notices: [], featured: [], destinations: [] })
  const [form, setForm] = useState(emptyNotice)
  const [editing, setEditing] = useState(null)
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)

  const load = async (query = search) => {
    setLoading(true)
    try {
      const { data } = await adminApi.getVisitorDesk({ q: query })
      setDesk({
        queue: data.queue || {},
        notices: data.notices || [],
        featured: data.featured || [],
        destinations: data.destinations || [],
      })
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load visitor desk", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const saveNotice = async (event) => {
    event.preventDefault()
    const payload = {
      ...form,
      destination_id: form.destination_id || null,
      starts_at: form.starts_at ? new Date(form.starts_at).toISOString() : undefined,
      ends_at: form.ends_at ? new Date(form.ends_at).toISOString() : null,
    }
    try {
      if (editing) await adminApi.updateVisitorNotice({ ...payload, id: editing })
      else await adminApi.createVisitorNotice(payload)
      showToast(editing ? "Notice updated" : "Notice saved", "success")
      setForm(emptyNotice)
      setEditing(null)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save notice", "error")
    }
  }

  const editNotice = (notice) => {
    setEditing(notice.id)
    setForm({
      title: notice.title || "",
      kind: notice.kind || "info",
      body: notice.body || "",
      city: notice.city || "",
      district: notice.district || "",
      destination_id: notice.destination_id || "",
      starts_at: toLocalInput(notice.starts_at),
      ends_at: toLocalInput(notice.ends_at),
      is_published: Boolean(notice.is_published),
    })
  }

  const removeNotice = async (id) => {
    if (!window.confirm("Remove this visitor notice?")) return
    try {
      await adminApi.deleteVisitorNotice(id)
      showToast("Notice removed", "success")
      if (editing === id) { setEditing(null); setForm(emptyNotice) }
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not remove notice", "error")
    }
  }

  const setFeatured = async (destinationId, isFeatured) => {
    try {
      const { data } = await adminApi.setFeaturedDestination(destinationId, isFeatured)
      showToast(data.message || "Featured places updated", "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not update featured place", "error")
    }
  }

  const queue = desk.queue || {}

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-wider text-emerald-700">Owner desk</p>
            <h2 className="text-2xl font-black text-slate-900">Visitor notices & featured places</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Publish what a traveller actually needs before they go — festivals, trail closures, permits, seasonal
              crowds — and pin the places your organisation wants on the homepage.
            </p>
          </div>
          <button type="button" onClick={() => load()} className="px-4 py-2 rounded-xl border border-emerald-200 text-emerald-800 text-sm font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mt-5">
          {[
            ["Pending places", queue.pending_places, "/admin?section=places", FiMapPin],
            ["Pending photos", queue.pending_images, "/admin?section=images", FiImage],
            ["Active SOS", queue.active_sos, "/admin?section=emergencies", FiAlertTriangle],
            ["Open feedback", queue.open_feedback, "/admin?section=feedback_workspace", FiMessageSquare],
            ["Published notices", queue.published_notices, null, FiCheck],
            ["Pinned places", queue.featured_places, null, FiStar],
          ].map(([label, value, href, Icon]) => {
            const card = (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[10px] uppercase font-black text-slate-500 flex items-center gap-1"><Icon size={12} /> {label}</p>
                <p className="text-2xl font-black text-slate-900 mt-1">{value ?? 0}</p>
              </div>
            )
            return href ? <Link key={label} to={href}>{card}</Link> : <div key={label}>{card}</div>
          })}
        </div>
      </div>

      <div className="grid xl:grid-cols-[380px_1fr] gap-5">
        <form onSubmit={saveNotice} className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="font-black text-slate-900">{editing ? "Edit notice" : "New visitor notice"}</h3>
          <input className="input-field" required placeholder="Title travellers will see" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <select className="input-field" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            {KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <textarea className="input-field min-h-[110px]" placeholder="What should a tourist do or know?" value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            <input className="input-field" placeholder="District" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
          </div>
          <input className="input-field" placeholder="Optional destination ID" value={form.destination_id} onChange={(e) => setForm({ ...form, destination_id: e.target.value })} />
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
            <label>Starts<input type="datetime-local" className="input-field mt-1" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })} /></label>
            <label>Ends<input type="datetime-local" className="input-field mt-1" value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })} /></label>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
            Show on the public site
          </label>
          <div className="flex gap-2">
            <button type="submit" className="flex-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black py-2 flex items-center justify-center gap-2">
              <FiPlus /> {editing ? "Update notice" : "Publish notice"}
            </button>
            {editing && (
              <button type="button" onClick={() => { setEditing(null); setForm(emptyNotice) }} className="px-3 rounded-xl border border-slate-300 text-slate-600">
                <FiX />
              </button>
            )}
          </div>
        </form>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="font-black text-slate-900 mb-3">Published & draft notices</h3>
          <div className="space-y-2 max-h-[70vh] overflow-y-auto">
            {desk.notices.length === 0 && <p className="text-sm text-slate-500">No visitor notices yet. Add a festival, closure or permit so travellers see it on the homepage.</p>}
            {desk.notices.map((notice) => (
              <div key={notice.id} className="rounded-xl border border-slate-200 p-3 flex justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${kindTone[notice.kind] || kindTone.info}`}>{notice.kind}</span>
                    {!notice.is_published && <span className="text-[10px] font-bold text-slate-500">Draft</span>}
                    <h4 className="font-bold text-slate-900">{notice.title}</h4>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 line-clamp-2">{notice.body}</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    {[notice.destination_name, notice.city, notice.district].filter(Boolean).join(" · ") || "All Nepal"}
                  </p>
                </div>
                <div className="shrink-0 flex flex-col gap-1">
                  <button type="button" onClick={() => editNotice(notice)} className="text-xs font-bold text-amber-700">Edit</button>
                  <button type="button" onClick={() => removeNotice(notice.id)} className="text-xs font-bold text-rose-600 flex items-center gap-1"><FiTrash2 /> Remove</button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
          <div>
            <h3 className="font-black text-slate-900">Pin featured destinations</h3>
            <p className="text-sm text-slate-600">Pinned places replace the rating heuristic on the landing page and traveller dashboard.</p>
          </div>
          <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); load(search) }}>
            <input className="input-field" placeholder="Search places to pin…" value={search} onChange={(e) => setSearch(e.target.value)} />
            <button type="submit" className="px-4 rounded-xl bg-amber-400 text-gray-950 font-black">Search</button>
          </form>
        </div>
        {desk.featured.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {desk.featured.map((place) => (
              <button key={place.id} type="button" onClick={() => setFeatured(place.id, false)} className="px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-900 text-xs font-bold flex items-center gap-1">
                <FiStar /> {place.name} <FiX />
              </button>
            ))}
          </div>
        )}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {desk.destinations.map((place) => (
            <div key={place.id} className="rounded-xl border border-slate-200 p-3 flex items-start justify-between gap-2">
              <div>
                <p className="font-bold text-slate-900">{place.name}</p>
                <p className="text-xs text-slate-500">{[place.district, place.city].filter(Boolean).join(" · ") || "Nepal"} · {place.average_rating}★</p>
              </div>
              <button
                type="button"
                onClick={() => setFeatured(place.id, !place.is_featured)}
                className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-black ${place.is_featured ? "bg-rose-100 text-rose-700" : "bg-emerald-600 text-white"}`}
              >
                {place.is_featured ? "Unpin" : "Pin"}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
