import { useEffect, useState, useRef } from "react"
import { Link } from "react-router-dom"
import { FiPlus, FiRefreshCw, FiRadio, FiShield, FiAlertTriangle, FiEdit3 } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const KINDS = [
  ["hospital", "Hospital / clinic"],
  ["police", "Police station"],
  ["pharmacy", "Pharmacy"],
  ["fire_station", "Fire & rescue"],
  ["ambulance", "Ambulance"],
  ["blood_bank", "Blood bank"],
]

const empty = {
  kind: "hospital", name: "", phone: "", address: "", city: "",
  district: "", province: "", latitude: "", longitude: "", source_url: "", opening_hours: "",
}

export default function EmergencyDirectoryPanel() {
  const { showToast } = useToast()
  const [form, setForm] = useState(empty)
  const [rows, setRows] = useState([])
  const [pending, setPending] = useState([])
  const [coverage, setCoverage] = useState({})
  const [query, setQuery] = useState("")
  const [kind, setKind] = useState("")
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [editing, setEditing] = useState(null)
  const [editForm, setEditForm] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdatedSec, setLastUpdatedSec] = useState(0)

  const prevPendingCount = useRef(0)

  const load = async (isBackground = false) => {
    if (!isBackground) setLoading(true)
    try {
      const { data } = await adminApi.getEmergencyDirectory({ q: query, kind, page, page_size: 50 })
      setRows(data.results || [])
      setPages(data.pages || 1)
      const newPending = data.pending_submissions || []
      setPending(newPending)
      setCoverage(data.coverage || {})

      if (isBackground && newPending.length > prevPendingCount.current) {
        showToast(`🚨 New community emergency submission received! (${newPending.length} pending)`, "warning")
      }
      prevPendingCount.current = newPending.length
      setLastUpdatedSec(0)
    } catch (error) {
      if (!isBackground) showToast(error.response?.data?.detail || "Could not load emergency directory", "error")
    } finally {
      if (!isBackground) setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [kind])

  // Live 5-second polling interval + timer counter
  useEffect(() => {
    const pollTimer = setInterval(() => {
      load(true)
    }, 5000)

    const secTimer = setInterval(() => {
      setLastUpdatedSec((prev) => prev + 1)
    }, 1000)

    return () => {
      clearInterval(pollTimer)
      clearInterval(secTimer)
    }
  }, [query, kind])

  const save = async (event) => {
    event.preventDefault()
    try {
      const { data } = await adminApi.createEmergencyDirectory(form)
      showToast(data.message || "Saved", "success")
      setForm(empty)
      load()
    } catch (error) {
      if (error.response?.status === 409) {
        showToast(error.response.data.detail || "This facility is already in the directory", "error")
      } else {
        showToast(error.response?.data?.detail || "Could not save record", "error")
      }
    }
  }

  const openEdit = (row) => {
    setEditing(row)
    setEditForm({
      name: row.name || "", phone: row.phone || "", address: row.address || "",
      district: row.district || "", opening_hours: row.opening_hours || "",
      source_name: row.source_name || "", source_url: row.source_url || "",
      latitude: row.latitude ?? "", longitude: row.longitude ?? "",
    })
  }

  const saveEdit = async (event) => {
    event.preventDefault()
    try {
      await adminApi.updateEmergencyDirectory({ kind: editing.kind, id: editing.id, ...editForm, action: "update" })
      showToast("Emergency record updated", "success")
      setEditing(null)
      load(page)
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not update record", "error")
    }
  }

  const act = async (row, action) => {
    try {
      const { data } = await adminApi.updateEmergencyDirectory({ kind: row.kind, id: row.id, action })
      showToast(data.message || "Updated", "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not update record", "error")
    }
  }

  return (
    <div className="space-y-6" data-testid="emergency-directory-panel">
      <div className="rounded-2xl border border-rose-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <p className="text-[11px] font-black uppercase tracking-wider text-rose-700">Safety</p>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 text-[10px] font-bold flex items-center gap-1">
                <FiRadio className="animate-pulse text-emerald-600" /> Live 5s Polling · Updated {lastUpdatedSec}s ago
              </span>
            </div>
            <h2 className="text-2xl font-black text-slate-900 mt-1">Emergency directory</h2>
            <p className="text-sm text-slate-500 mt-1 max-w-3xl">
              Add accurate hospitals, police, pharmacies or fire stations with coordinates.
              Saves to the database and appends the official CSV. This does not scrape Google or Facebook,
              and it does not invent 50–60 pharmacies per ward.
            </p>
          </div>
          <button type="button" onClick={() => load(false)} className="px-4 py-2 rounded-xl border border-rose-200 text-rose-800 text-sm font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        <div className="flex flex-wrap gap-3 mt-4 text-xs font-bold text-slate-600">
          <span>Hospitals: <b>{coverage.hospitals ?? "—"}</b></span>
          <span>Police: <b>{coverage.police ?? "—"}</b></span>
          <span>Pharmacies: <b>{coverage.pharmacy ?? "—"}</b></span>
          <span>Fire & Rescue: <b>{coverage.fire_station ?? "—"}</b></span>
        </div>
        <form className="flex gap-2 mt-3" onSubmit={(event) => { event.preventDefault(); load(false) }}>
          <input className="input-field" placeholder="Search Dadeldhura, Amargadhi, pharmacy…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <select className="input-field max-w-[180px]" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="">All types</option>
            {KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <button type="submit" className="px-4 rounded-xl bg-rose-700 text-white font-black">Search</button>
        </form>
      </div>

      {pending.length > 0 && (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <h3 className="font-black text-slate-900 mb-2 flex items-center gap-1.5"><FiAlertTriangle className="text-amber-600" /> Pending community submissions ({pending.length})</h3>
          <p className="text-xs text-slate-500 mb-3">These stay hidden until an administrator verifies them. Approve from Infrastructure, or add the verified row here.</p>
          <div className="space-y-2">
            {pending.map((row) => (
              <div key={row.id} className="rounded-xl border border-amber-200 bg-white p-3">
                <p className="font-bold text-slate-900">{row.name}</p>
                <p className="text-xs text-slate-500">{row.kind} · {row.district || "Nepal"} · {row.status} · {row.phone || "no phone"}</p>
              </div>
            ))}
          </div>
          <Link to="/submit-service" className="inline-block mt-3 text-xs font-black text-rose-800 underline">Open public submit form</Link>
        </section>
      )}

      <div className="grid xl:grid-cols-[360px_1fr] gap-5">
        <form onSubmit={save} className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="font-black text-slate-900">Add a verified local service</h3>
          <select className="input-field" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            {KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <input className="input-field" required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input-field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="input-field" placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" placeholder="District (e.g. Dadeldhura)" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
            <input className="input-field" placeholder="Province" value={form.province} onChange={(e) => setForm({ ...form, province: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" required placeholder="Latitude" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
            <input className="input-field" required placeholder="Longitude" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
          </div>
          <input className="input-field" placeholder="HTTPS source URL (optional)" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} />
          <button type="submit" className="w-full rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-black py-2 flex items-center justify-center gap-2">
            <FiPlus /> Save to database & CSV
          </button>
        </form>
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="font-black text-slate-900 mb-3">Directory rows</h3>
          <div className="space-y-2 max-h-[80vh] overflow-y-auto">
            {rows.length === 0 && <p className="text-sm text-slate-500">No matching records. Add an accurate row for this district.</p>}
            {rows.map((row) => (
              <div key={`${row.kind}-${row.id}`} className="rounded-xl border border-slate-200 p-3">
                <p className="font-bold text-slate-900">{row.name}</p>
                <p className="text-xs text-slate-500">{row.kind} · {row.district || row.destination_name || "Nepal"} · {row.phone || "no phone"}{row.is_archived ? " · archived" : ""}{row.verified ? " · verified" : ""}</p>
                <p className="text-xs text-slate-500">{row.latitude}, {row.longitude}</p>
                 <p className="text-[10px] text-slate-400">Source: {row.source_name || "Not recorded"} · Updated {row.updated_at ? new Date(row.updated_at).toLocaleString() : "unknown"}</p>
                 <div className="flex gap-2 mt-2">
                   <button type="button" onClick={() => openEdit(row)} className="inline-flex items-center gap-1 text-xs font-bold text-slate-700"><FiEdit3 /> Edit</button>
                  {!row.verified && <button type="button" onClick={() => act(row, "verify")} className="text-xs font-bold text-emerald-700">Verify</button>}
                  {!row.is_archived && <button type="button" onClick={() => act(row, "archive")} className="text-xs font-bold text-rose-700">Archive</button>}
                  {row.is_archived && <button type="button" onClick={() => act(row, "restore")} className="text-xs font-bold text-slate-700">Restore</button>}
                </div>
              </div>
            ))}
          </div>
        </section>
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
          <span>Page {page} of {pages}</span>
          <div className="flex gap-2">
            <button type="button" disabled={page <= 1 || loading} onClick={() => { const next = page - 1; setPage(next); load(next) }} className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40">Previous</button>
            <button type="button" disabled={page >= pages || loading} onClick={() => { const next = page + 1; setPage(next); load(next) }} className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40">Next</button>
          </div>
        </div>
      </div>
      {editing && (
        <div className="fixed inset-0 z-[100] grid place-items-center bg-black/60 p-4">
          <form onSubmit={saveEdit} className="w-full max-w-2xl space-y-3 rounded-2xl bg-white p-6 text-slate-900 shadow-2xl">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div><p className="text-[10px] font-black uppercase text-rose-700">Emergency record</p><h3 className="text-xl font-black">Edit {editing.name}</h3></div>
              <button type="button" onClick={() => setEditing(null)} className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold" aria-label="Close editor">Close</button>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-bold">Name<input required className="input-field mt-1" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></label>
              <label className="text-xs font-bold">Phone<input required className="input-field mt-1" value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} /></label>
              <label className="text-xs font-bold sm:col-span-2">Address<input className="input-field mt-1" value={editForm.address} onChange={(e) => setEditForm({ ...editForm, address: e.target.value })} /></label>
              <label className="text-xs font-bold">District<input className="input-field mt-1" value={editForm.district} onChange={(e) => setEditForm({ ...editForm, district: e.target.value })} /></label>
              <label className="text-xs font-bold">Opening hours<input className="input-field mt-1" value={editForm.opening_hours} onChange={(e) => setEditForm({ ...editForm, opening_hours: e.target.value })} /></label>
              <label className="text-xs font-bold">Source name<input className="input-field mt-1" value={editForm.source_name} onChange={(e) => setEditForm({ ...editForm, source_name: e.target.value })} /></label>
              <label className="text-xs font-bold">Source URL<input type="url" className="input-field mt-1" value={editForm.source_url} onChange={(e) => setEditForm({ ...editForm, source_url: e.target.value })} /></label>
              <label className="text-xs font-bold">Latitude<input required type="number" step="any" className="input-field mt-1" value={editForm.latitude} onChange={(e) => setEditForm({ ...editForm, latitude: e.target.value })} /></label>
              <label className="text-xs font-bold">Longitude<input required type="number" step="any" className="input-field mt-1" value={editForm.longitude} onChange={(e) => setEditForm({ ...editForm, longitude: e.target.value })} /></label>
            </div>
            <p className="text-[11px] text-slate-500">Changes are saved to the existing record and audited. Verification remains a separate action.</p>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setEditing(null)} className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-bold">Cancel</button><button type="submit" className="rounded-xl bg-rose-700 px-5 py-2 text-xs font-black text-white">Save changes</button></div>
          </form>
        </div>
      )}
    </div>
  )
}
