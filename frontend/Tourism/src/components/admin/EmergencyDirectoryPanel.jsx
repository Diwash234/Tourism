import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiPlus, FiRefreshCw } from "react-icons/fi"
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
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await adminApi.getEmergencyDirectory({ q: query, kind })
      setRows(data.results || [])
      setPending(data.pending_submissions || [])
      setCoverage(data.coverage || {})
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load emergency directory", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [kind])

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
            <p className="text-[11px] font-black uppercase tracking-wider text-rose-700">Safety</p>
            <h2 className="text-2xl font-black text-slate-900">Emergency directory</h2>
            <p className="text-sm text-slate-300 mt-1 max-w-3xl">
              Add accurate hospitals, police, pharmacies or fire stations with coordinates.
              Saves to the database and appends the official CSV. This does not scrape Google or Facebook,
              and it does not invent 50–60 pharmacies per ward.
            </p>
          </div>
          <button type="button" onClick={load} className="px-4 py-2 rounded-xl border border-rose-200 text-rose-800 text-sm font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        <div className="flex flex-wrap gap-3 mt-4 text-xs font-bold text-slate-300">
          <span>Hospitals {coverage.hospitals ?? "—"}</span>
          <span>Police {coverage.police ?? "—"}</span>
          <span>Pharmacies {coverage.pharmacy ?? "—"}</span>
          <span>Fire {coverage.fire_station ?? "—"}</span>
        </div>
        <form className="flex gap-2 mt-3" onSubmit={(event) => { event.preventDefault(); load() }}>
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
          <h3 className="font-black text-slate-900 mb-2">Pending community submissions</h3>
          <p className="text-xs text-slate-300 mb-3">These stay hidden until an administrator verifies them. Approve from Infrastructure, or add the verified row here.</p>
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
                <p className="text-xs text-slate-300">{row.latitude}, {row.longitude}</p>
                <div className="flex gap-2 mt-2">
                  {!row.verified && <button type="button" onClick={() => act(row, "verify")} className="text-xs font-bold text-emerald-700">Verify</button>}
                  {!row.is_archived && <button type="button" onClick={() => act(row, "archive")} className="text-xs font-bold text-rose-700">Archive</button>}
                  {row.is_archived && <button type="button" onClick={() => act(row, "restore")} className="text-xs font-bold text-slate-700">Restore</button>}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
