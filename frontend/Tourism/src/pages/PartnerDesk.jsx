import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiBriefcase } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import destinationApi from "../api/destinationApi"
import useToast from "../hooks/useToast"

const LISTING_KINDS = [
  ["package", "Travel package"],
  ["hotel", "Hotel / stay"],
  ["tour", "Tour"],
  ["activity", "Activity"],
  ["transfer", "Transfer"],
  ["restaurant", "Food experience"],
  ["guide", "Guide"],
]

const empty = {
  kind: "package", title: "", summary: "", description: "", includes: "", excludes: "",
  duration_days: 1, price_npr: "", image_url: "", external_url: "", city: "", district: "",
  cancellation_policy: "", capacity: 10, destination_id: "",
}

export default function PartnerDesk() {
  const { showToast } = useToast()
  const [desk, setDesk] = useState(null)
  const [missing, setMissing] = useState(false)
  const [destinations, setDestinations] = useState([])
  const [form, setForm] = useState(empty)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try {
      const [{ data }, destRes] = await Promise.all([
        userApi.getPartnerDesk(),
        destinationApi.getAll({ page_size: 80 }),
      ])
      setDesk(data)
      setMissing(false)
      const destList = destRes.data?.results || destRes.data || []
      setDestinations(Array.isArray(destList) ? destList : [])
    } catch (error) {
      if (error.response?.status === 404) setMissing(true)
      else showToast(error.response?.data?.detail || "Could not load partner desk", "error")
    }
  }

  useEffect(() => { load() }, [])

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    try {
      const { data } = await userApi.createPartnerListing({
        ...form,
        destination_id: form.destination_id || null,
        status: "published",
      })
      showToast(data.message || "Submitted for review", "success")
      setForm(empty)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save package", "error")
    } finally {
      setBusy(false)
    }
  }

  if (missing) {
    return (
      <div className="container-app py-10">
        <PageHeader title="Partner desk" subtitle="Apply first. After an administrator approves your business you can add packages here." icon={FiBriefcase} theme="forest" />
        <div className="card-base p-6 max-w-xl space-y-3">
          <p className="text-slate-600">No partner application is linked to this account.</p>
          <Link to="/collaborate" className="btn-primary inline-flex">Apply to partner</Link>
        </div>
      </div>
    )
  }

  if (!desk) return <div className="container-app py-16 text-sm text-slate-500">Loading partner desk…</div>

  const partner = desk.partner || {}

  return (
    <div className="container-app py-10 space-y-6">
      <PageHeader
        title="Partner desk"
        subtitle="Add or edit packages. An administrator reviews each offer and publishes it. You cannot publish yourself."
        icon={FiBriefcase}
        theme="forest"
      />
      <section className="card-base p-5">
        <p className="text-xs font-black uppercase text-emerald-800">{partner.kind}</p>
        <h2 className="text-2xl font-black">{partner.name}</h2>
        <p className="text-sm text-slate-600">Status: <b>{partner.status}</b> · {partner.email}</p>
        {desk.message && <p className="mt-2 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl p-3">{desk.message}</p>}
      </section>

      {desk.can_manage_listings && (
        <div className="grid xl:grid-cols-[360px_1fr] gap-5">
          <form onSubmit={submit} className="card-base p-5 space-y-3">
            <h3 className="font-black">Submit a package for review</h3>
            <select className="input-field" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              {LISTING_KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
            <select className="input-field" value={form.destination_id} onChange={(e) => setForm({ ...form, destination_id: e.target.value })}>
              <option value="">Optional destination…</option>
              {destinations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
            </select>
            <input className="input-field" required placeholder="Title travellers will see" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <input className="input-field" placeholder="Short summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
            <textarea className="input-field" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input-field" required placeholder="Price NPR" value={form.price_npr} onChange={(e) => setForm({ ...form, price_npr: e.target.value })} />
              <input className="input-field" type="number" min="1" placeholder="Days" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
            </div>
            <input className="input-field" placeholder="HTTPS image URL" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} />
            <input className="input-field" placeholder="Partner HTTPS booking URL" value={form.external_url} onChange={(e) => setForm({ ...form, external_url: e.target.value })} />
            <button type="submit" disabled={busy} className="btn-primary w-full">{busy ? "Sending…" : "Submit for review"}</button>
          </form>
          <section className="card-base p-5 space-y-3">
            <h3 className="font-black">Your offers</h3>
            {(desk.listings || []).length === 0 && <p className="text-sm text-slate-500">No packages yet.</p>}
            {(desk.listings || []).map((row) => (
              <div key={row.id} className="rounded-xl border border-slate-200 p-3">
                <p className="font-bold">{row.title}</p>
                <p className="text-xs text-slate-500">{row.kind} · NPR {row.price_npr} · {row.status}{row.is_featured ? " · featured" : ""}</p>
                {row.status === "pending" && <p className="text-xs text-amber-800 mt-1">Waiting for an administrator to publish.</p>}
              </div>
            ))}
          </section>
        </div>
      )}

      {(desk.orders || []).length > 0 && (
        <section className="card-base p-5 space-y-3">
          <h3 className="font-black">Incoming trip requests</h3>
          {desk.orders.map((row) => (
            <div key={row.id} className="rounded-xl border border-slate-200 p-3">
              <p className="font-bold">{row.reference} · {row.status}</p>
              <p className="text-xs text-slate-500">{row.guest_name} · {row.guest_email} · NPR {row.total_npr}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
