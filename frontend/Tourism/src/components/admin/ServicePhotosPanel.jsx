import { useEffect, useState } from "react"
import { BsBuilding, BsFire, BsHospital, BsShieldLock, BsTrash, BsUpload } from "react-icons/bs"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const KINDS = [
  { id: "", label: "All emergency services" },
  { id: "hospital", label: "Hospitals" },
  { id: "police", label: "Police stations" },
  { id: "essential", label: "Fire, banks & OSM services" },
]

const CATEGORIES = [
  { id: "", label: "All OSM categories" },
  { id: "hospital", label: "Hospital" },
  { id: "clinic", label: "Clinic" },
  { id: "police", label: "Police" },
  { id: "fire_station", label: "Fire station" },
  { id: "bank", label: "Bank" },
  { id: "blood_bank", label: "Blood bank" },
  { id: "ambulance", label: "Ambulance" },
]

const kindIcon = (row) => {
  const category = String(row.category || row.kind || "")
  if (category.includes("fire")) return BsFire
  if (category.includes("police")) return BsShieldLock
  if (category.includes("bank")) return BsBuilding
  return BsHospital
}

export default function ServicePhotosPanel() {
  const { showToast } = useToast()
  const [kind, setKind] = useState("")
  const [category, setCategory] = useState("")
  const [q, setQ] = useState("")
  const [rows, setRows] = useState([])
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(null)

  const load = async () => {
    setBusy(true)
    try {
      const params = { q }
      if (kind) params.kind = kind
      if (kind === "essential" && category) params.category = category
      const { data } = await adminApi.getServiceMedia(params)
      setRows(data.results || [])
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load service photos", "error")
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { load() }, [kind, category]) // eslint-disable-line react-hooks/exhaustive-deps

  const upload = async (row, file) => {
    if (!file) return
    setUploading(`${row.kind}-${row.id}`)
    const body = new FormData()
    body.append("kind", row.kind)
    body.append("id", row.id)
    body.append("file", file)
    try {
      await adminApi.uploadServiceMedia(body)
      showToast("Photo saved for Emergency pages", "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Upload failed", "error")
    } finally {
      setUploading(null)
    }
  }

  const remove = async (row) => {
    if (!window.confirm(`Remove the photo for ${row.name}?`)) return
    try {
      await adminApi.deleteServiceMedia({ kind: row.kind, id: row.id })
      showToast("Photo removed", "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not remove photo", "error")
    }
  }

  return (
    <section className="space-y-4 rounded-2xl border border-emerald-200 bg-white p-5 text-slate-900">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-xl font-black text-emerald-950">Emergency service photos</h2>
          <p className="text-sm text-slate-600">Add hospital, police, fire station and bank photos. Travellers see them on the Emergency page.</p>
        </div>
        <button type="button" onClick={load} className="ml-auto rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white">Refresh</button>
      </header>
      <div className="grid gap-2 sm:grid-cols-4">
        <select className="input-field" value={kind} onChange={(event) => setKind(event.target.value)}>
          {KINDS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <select className="input-field" value={category} onChange={(event) => setCategory(event.target.value)} disabled={kind !== "essential"}>
          {CATEGORIES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <input className="input-field sm:col-span-2" value={q} onChange={(event) => setQ(event.target.value)} onKeyDown={(event) => event.key === "Enter" && load()} placeholder="Search name, address or destination…" />
      </div>
      {busy ? <p className="text-sm text-slate-600">Loading services…</p> : null}
      {!busy && !rows.length ? <p className="rounded-xl border border-dashed border-emerald-200 p-6 text-center text-sm text-slate-500">No matching hospitals, police stations, fire stations or banks.</p> : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((row) => {
          const Icon = kindIcon(row)
          const key = `${row.kind}-${row.id}`
          return (
            <article key={key} className="overflow-hidden rounded-2xl border border-emerald-100 bg-emerald-50/40">
              {row.image_url
                ? <img src={row.image_url} alt={row.name} className="h-36 w-full object-cover" />
                : <div className="flex h-36 items-center justify-center bg-emerald-100 text-emerald-800"><Icon className="text-3xl" /></div>}
              <div className="space-y-2 p-3 text-xs text-slate-700">
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-800">{row.kind} · {row.category}</p>
                <h3 className="truncate text-sm font-black text-slate-900">{row.name}</h3>
                <p className="truncate">{row.destination || row.address || "Nepal"}</p>
                <p>{row.phone || "Phone not listed"}</p>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <label className="cursor-pointer rounded-lg bg-emerald-700 px-2 py-2 text-center font-bold text-white">
                    <BsUpload className="mr-1 inline" />{uploading === key ? "Saving…" : "Upload"}
                    <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(event) => upload(row, event.target.files?.[0])} />
                  </label>
                  <button type="button" disabled={!row.has_image} onClick={() => remove(row)} className="rounded-lg bg-rose-100 px-2 py-2 font-bold text-rose-800 disabled:opacity-40">
                    <BsTrash className="mr-1 inline" />Remove
                  </button>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
