import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiBriefcase } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import destinationApi from "../api/destinationApi"
import useToast from "../hooks/useToast"
import CMSPageIntro from "../components/cms/CMSPageIntro"

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
  const [loadError, setLoadError] = useState("")
  const [loading, setLoading] = useState(true)
  const [destinations, setDestinations] = useState([])
  const [form, setForm] = useState(empty)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    setLoading(true)
    setLoadError("")
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
      else {
        setLoadError(error.response?.data?.detail || "We could not load the partner desk right now.")
        showToast(error.response?.data?.detail || "Could not load partner desk", "error")
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    try {
      const { data } = await userApi.createPartnerListing({
        ...form,
        destination_id: form.destination_id || null,
        status: "pending",
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

  if (loading && !missing && !loadError) return <div className="ny-page container-app py-16 text-sm text-[var(--ny-text-secondary)]">Loading partner desk…</div>

  if (missing) {
    return (
      <div className="ny-page container-app space-y-6 py-6 sm:py-8">
        <CMSPageIntro pageKey="partner-desk" />
        <PageHeader title="Partner desk" subtitle="Apply first. After an administrator approves your business you can add packages here." icon={FiBriefcase} theme="forest" />
        <div data-testid="partner-desk-missing" />
        <div className="card-base p-6 max-w-xl space-y-3">
          <p className="text-slate-600">No partner application is linked to this account.</p>
          <Link to="/collaborate" className="btn-primary inline-flex">Apply to partner</Link>
        </div>
      </div>
    )
  }

  if (loadError) {
    return <div className="ny-page container-app py-16"><div className="ny-panel mx-auto max-w-xl p-6 text-center" role="alert"><p className="font-bold text-[var(--ny-danger)]">Partner desk unavailable</p><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{loadError}</p><button type="button" onClick={load} className="ny-btn ny-btn-secondary mt-4">Try again</button></div></div>
  }

  if (!desk) return <div className="ny-page container-app py-16 text-sm text-[var(--ny-text-secondary)]">Loading partner desk…</div>

  const partner = desk.partner || {}

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8" data-testid="partner-desk">
      <PageHeader
        title="Partner desk"
        subtitle="Add or edit packages. An administrator reviews each offer and publishes it. You cannot publish yourself."
        icon={FiBriefcase}
        theme="forest"
      />
      <section className="card-base p-5">
        <p className="text-xs font-black uppercase text-emerald-800">{partner.kind || "Partner type unavailable"}</p>
        <h2 className="text-2xl font-black">{partner.name || "Partner record"}</h2>
        <p className="text-sm text-slate-600">Status: <b>{partner.status || "Unavailable"}</b> · {partner.email || "Email unavailable"}</p>
        {desk.message && <p className="mt-2 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl p-3">{desk.message}</p>}
      </section>

      {desk.can_manage_listings && (
        <div className="grid xl:grid-cols-[360px_1fr] gap-5">
          <form onSubmit={submit} className="card-base p-5 space-y-3" data-testid="partner-listing-form">
            <h3 className="font-black">Submit a package for review</h3>
            <select aria-label="Listing type" className="input-field" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              {LISTING_KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
            <select aria-label="Destination" className="input-field" value={form.destination_id} onChange={(e) => setForm({ ...form, destination_id: e.target.value })}>
              <option value="">Optional destination…</option>
              {destinations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
            </select>
            <input aria-label="Listing title" className="input-field" required name="title" data-testid="partner-listing-title" placeholder="Title travellers will see" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <input aria-label="Listing summary" className="input-field" placeholder="Short summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
            <textarea aria-label="Listing description" className="input-field" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input aria-label="Price in NPR" className="input-field" required name="price_npr" data-testid="partner-listing-price" placeholder="Price NPR" value={form.price_npr} onChange={(e) => setForm({ ...form, price_npr: e.target.value })} />
              <input aria-label="Duration in days" className="input-field" type="number" min="1" placeholder="Days" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
            </div>
            <input aria-label="HTTPS image URL" className="input-field" placeholder="HTTPS image URL" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} />
            <input aria-label="Partner booking URL" className="input-field" placeholder="Partner HTTPS booking URL" value={form.external_url} onChange={(e) => setForm({ ...form, external_url: e.target.value })} />
            <button type="submit" disabled={busy} data-testid="partner-listing-submit" className="btn-primary w-full">{busy ? "Sending…" : "Submit for review"}</button>
          </form>
          <section className="card-base p-5 space-y-3">
            <h3 className="font-black">Your offers</h3>
            {(desk.listings || []).length === 0 && <p className="text-sm text-slate-500">No packages yet.</p>}
            {(desk.listings || []).map((row) => (
              <div key={row.id} className="rounded-xl border border-slate-200 p-3">
                <p className="font-bold">{row.title}</p>
                <p className="text-xs text-slate-500">{row.kind || "Offer"} · {row.price_npr != null ? `NPR ${row.price_npr}` : "Price unavailable"} · {row.status || "Status unavailable"}{row.is_featured ? " · featured" : ""}</p>
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
              <p className="text-xs text-slate-500">{row.guest_name || "Guest unavailable"} · {row.guest_email || "Email unavailable"} · {row.total_npr != null ? `NPR ${row.total_npr}` : "Total unavailable"}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
