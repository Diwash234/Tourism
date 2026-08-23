import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiCheck, FiPlus, FiRefreshCw, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const TABS = [
  ["listings", "Offers"],
  ["partners", "Partners"],
  ["orders", "Trip requests"],
]

const PARTNER_KINDS = [
  ["hotel", "Hotel / stay"],
  ["operator", "Tour operator"],
  ["guide", "Local guide"],
  ["restaurant", "Restaurant"],
  ["transport", "Transport"],
  ["activity", "Activity provider"],
  ["agency", "Travel agency"],
]

const LISTING_KINDS = [
  ["package", "Travel package"],
  ["hotel", "Hotel / stay"],
  ["tour", "Tour"],
  ["activity", "Activity"],
  ["transfer", "Transfer"],
  ["restaurant", "Food experience"],
  ["guide", "Guide"],
  ["ad", "Sponsored offer"],
]

const emptyPartner = { name: "", kind: "operator", email: "", contact_name: "", phone: "", website: "", city: "", district: "", description: "", status: "approved" }
const emptyListing = { partner_id: "", destination_id: "", kind: "package", title: "", summary: "", description: "", includes: "", excludes: "", duration_days: 1, price_npr: "", image_url: "", external_url: "", city: "", district: "", cancellation_policy: "", capacity: 10, is_featured: false, status: "published" }

export default function MarketplacePanel() {
  const { showToast } = useToast()
  const [tab, setTab] = useState("listings")
  const [rows, setRows] = useState([])
  const [partners, setPartners] = useState([])
  const [destinations, setDestinations] = useState([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [partnerForm, setPartnerForm] = useState(emptyPartner)
  const [listingForm, setListingForm] = useState(emptyListing)

  const load = async (resource = tab, q = query) => {
    setLoading(true)
    try {
      const [{ data }, destRes] = await Promise.all([
        adminApi.getMarketplace({ resource, q }),
        adminApi.getDestinations({ page_size: 80 }),
      ])
      setRows(data.results || [])
      const destList = destRes.data?.results || destRes.data || []
      setDestinations(Array.isArray(destList) ? destList : [])
      if (resource !== "partners") {
        const partnerRes = await adminApi.getMarketplace({ resource: "partners" })
        setPartners(partnerRes.data.results || [])
      } else {
        setPartners(data.results || [])
      }
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load marketplace", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(tab) }, [tab])

  const savePartner = async (event) => {
    event.preventDefault()
    try {
      await adminApi.createMarketplace({ resource: "partners", ...partnerForm })
      showToast("Partner saved", "success")
      setPartnerForm(emptyPartner)
      load("partners")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save partner", "error")
    }
  }

  const saveListing = async (event) => {
    event.preventDefault()
    try {
      await adminApi.createMarketplace({
        resource: "listings",
        ...listingForm,
        destination_id: listingForm.destination_id || null,
        is_featured: Boolean(listingForm.is_featured),
      })
      showToast("Offer published to packages", "success")
      setListingForm(emptyListing)
      load("listings")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save offer", "error")
    }
  }

  const act = async (payload, success) => {
    try {
      const { data } = await adminApi.updateMarketplace(payload)
      showToast(data.message || success, "success")
      load(tab)
    } catch (error) {
      showToast(error.response?.data?.detail || "Update failed", "error")
    }
  }

  const approvedPartners = partners.filter((row) => row.status === "approved")

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-black uppercase tracking-wider text-emerald-700">Travel services</p>
            <h2 className="text-2xl font-black text-slate-900">Packages, partners & trip requests</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              Add packages from this desk or after a hotel / operator applies. Travellers request to book or continue
              on the partner HTTPS site — card numbers are never stored here.
            </p>
          </div>
          <div className="flex gap-2">
            <Link to="/packages" className="px-4 py-2 rounded-xl border border-emerald-200 text-emerald-800 text-sm font-bold">View public page</Link>
            <button type="button" onClick={() => load()} className="px-4 py-2 rounded-xl border border-emerald-200 text-emerald-800 text-sm font-bold flex items-center gap-2">
              <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          {TABS.map(([id, label]) => (
            <button key={id} type="button" onClick={() => setTab(id)} className={`px-3 py-1.5 rounded-full text-xs font-black uppercase ${tab === id ? "bg-emerald-700 text-white" : "bg-emerald-50 text-emerald-900"}`}>
              {label}
            </button>
          ))}
        </div>
        <form className="flex gap-2 mt-3" onSubmit={(event) => { event.preventDefault(); load(tab, query) }}>
          <input className="input-field" placeholder="Search titles, partners, emails…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button type="submit" className="px-4 rounded-xl bg-emerald-700 text-white font-black">Search</button>
        </form>
      </div>

      {tab === "listings" && (
        <div className="grid xl:grid-cols-[360px_1fr] gap-5">
          <form onSubmit={saveListing} className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
            <h3 className="font-black text-slate-900">Add or publish an offer</h3>
            <select className="input-field" required value={listingForm.partner_id} onChange={(e) => setListingForm({ ...listingForm, partner_id: e.target.value })}>
              <option value="">Approved partner…</option>
              {approvedPartners.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
            </select>
            <select className="input-field" value={listingForm.destination_id} onChange={(e) => setListingForm({ ...listingForm, destination_id: e.target.value })}>
              <option value="">Optional destination…</option>
              {destinations.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}
            </select>
            <select className="input-field" value={listingForm.kind} onChange={(e) => setListingForm({ ...listingForm, kind: e.target.value })}>
              {LISTING_KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
            <input className="input-field" required placeholder="Title travellers will see" value={listingForm.title} onChange={(e) => setListingForm({ ...listingForm, title: e.target.value })} />
            <input className="input-field" placeholder="Short summary" value={listingForm.summary} onChange={(e) => setListingForm({ ...listingForm, summary: e.target.value })} />
            <textarea className="input-field min-h-[80px]" placeholder="Description" value={listingForm.description} onChange={(e) => setListingForm({ ...listingForm, description: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input-field" required placeholder="Price NPR" value={listingForm.price_npr} onChange={(e) => setListingForm({ ...listingForm, price_npr: e.target.value })} />
              <input className="input-field" type="number" min="1" placeholder="Days" value={listingForm.duration_days} onChange={(e) => setListingForm({ ...listingForm, duration_days: e.target.value })} />
            </div>
            <input className="input-field" placeholder="HTTPS image URL (optional)" value={listingForm.image_url} onChange={(e) => setListingForm({ ...listingForm, image_url: e.target.value })} />
            <input className="input-field" placeholder="Partner HTTPS booking URL (optional)" value={listingForm.external_url} onChange={(e) => setListingForm({ ...listingForm, external_url: e.target.value })} />
            <textarea className="input-field" placeholder="Includes" value={listingForm.includes} onChange={(e) => setListingForm({ ...listingForm, includes: e.target.value })} />
            <textarea className="input-field" placeholder="Excludes" value={listingForm.excludes} onChange={(e) => setListingForm({ ...listingForm, excludes: e.target.value })} />
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={listingForm.is_featured} onChange={(e) => setListingForm({ ...listingForm, is_featured: e.target.checked })} />
              Feature on packages page
            </label>
            <button type="submit" className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black py-2 flex items-center justify-center gap-2">
              <FiPlus /> Save offer
            </button>
            {approvedPartners.length === 0 && <p className="text-xs text-amber-800">Add and approve a partner first, or create one in the Partners tab.</p>}
          </form>
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="font-black text-slate-900 mb-3">All offers</h3>
            <div className="space-y-2 max-h-[80vh] overflow-y-auto">
              {rows.length === 0 && <p className="text-sm text-slate-500">No packages yet. Publish one and it appears on /packages immediately.</p>}
              {rows.map((row) => (
                <div key={row.id} className="rounded-xl border border-slate-200 p-3 flex justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">{row.title}</p>
                    <p className="text-xs text-slate-500">{row.kind} · {row.partner_name} · NPR {row.price_npr} · {row.status}</p>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">{row.summary}</p>
                  </div>
                  <div className="shrink-0 flex flex-col gap-1">
                    {row.status !== "published" && <button type="button" onClick={() => act({ resource: "listings", id: row.id, action: "publish" }, "Published")} className="text-xs font-bold text-emerald-700">Publish</button>}
                    {row.status === "published" && <button type="button" onClick={() => act({ resource: "listings", id: row.id, action: "archive" }, "Archived")} className="text-xs font-bold text-rose-700">Archive</button>}
                    <button type="button" onClick={() => act({ resource: "listings", id: row.id, is_featured: !row.is_featured }, "Updated")} className="text-xs font-bold text-amber-700">{row.is_featured ? "Unpin" : "Feature"}</button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "partners" && (
        <div className="grid xl:grid-cols-[360px_1fr] gap-5">
          <form onSubmit={savePartner} className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
            <h3 className="font-black text-slate-900">Add a partner</h3>
            <input className="input-field" required placeholder="Business name" value={partnerForm.name} onChange={(e) => setPartnerForm({ ...partnerForm, name: e.target.value })} />
            <select className="input-field" value={partnerForm.kind} onChange={(e) => setPartnerForm({ ...partnerForm, kind: e.target.value })}>
              {PARTNER_KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
            <input className="input-field" required type="email" placeholder="Email" value={partnerForm.email} onChange={(e) => setPartnerForm({ ...partnerForm, email: e.target.value })} />
            <input className="input-field" placeholder="Contact person" value={partnerForm.contact_name} onChange={(e) => setPartnerForm({ ...partnerForm, contact_name: e.target.value })} />
            <input className="input-field" placeholder="Phone" value={partnerForm.phone} onChange={(e) => setPartnerForm({ ...partnerForm, phone: e.target.value })} />
            <input className="input-field" placeholder="HTTPS website (optional)" value={partnerForm.website} onChange={(e) => setPartnerForm({ ...partnerForm, website: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input-field" placeholder="City" value={partnerForm.city} onChange={(e) => setPartnerForm({ ...partnerForm, city: e.target.value })} />
              <input className="input-field" placeholder="District" value={partnerForm.district} onChange={(e) => setPartnerForm({ ...partnerForm, district: e.target.value })} />
            </div>
            <textarea className="input-field" placeholder="About the business" value={partnerForm.description} onChange={(e) => setPartnerForm({ ...partnerForm, description: e.target.value })} />
            <button type="submit" className="w-full rounded-xl bg-emerald-600 text-white font-black py-2">Save partner</button>
          </form>
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="font-black text-slate-900 mb-3">Applications & partners</h3>
            <div className="space-y-2 max-h-[80vh] overflow-y-auto">
              {rows.map((row) => (
                <div key={row.id} className="rounded-xl border border-slate-200 p-3 flex justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">{row.name}</p>
                    <p className="text-xs text-slate-500">{row.kind} · {row.email} · {row.status} · {row.listing_count} offer(s)</p>
                    <p className="text-xs text-slate-600 mt-1">{[row.city, row.district].filter(Boolean).join(" · ")}</p>
                  </div>
                  <div className="shrink-0 flex flex-col gap-1">
                    {row.status !== "approved" && <button type="button" onClick={() => act({ resource: "partners", id: row.id, action: "approve" }, "Approved")} className="text-xs font-bold text-emerald-700 flex items-center gap-1"><FiCheck /> Approve</button>}
                    {row.status === "pending" && <button type="button" onClick={() => act({ resource: "partners", id: row.id, action: "reject" }, "Rejected")} className="text-xs font-bold text-rose-700 flex items-center gap-1"><FiX /> Reject</button>}
                    {row.status === "approved" && <button type="button" onClick={() => act({ resource: "partners", id: row.id, action: "suspend" }, "Suspended")} className="text-xs font-bold text-amber-700">Suspend</button>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "orders" && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 className="font-black text-slate-900 mb-3">Trip requests</h3>
          <p className="text-sm text-slate-600 mb-4">These are booking requests or hand-offs to partner sites. Confirm after the operator accepts payment offline.</p>
          <div className="space-y-3">
            {rows.length === 0 && <p className="text-sm text-slate-500">No trip requests yet.</p>}
            {rows.map((row) => (
              <div key={row.id} className="rounded-xl border border-slate-200 p-3">
                <div className="flex justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">{row.reference} · NPR {row.total_npr}</p>
                    <p className="text-xs text-slate-500">{row.guest_name} · {row.guest_email} · {row.status} · {row.payment_method}</p>
                  </div>
                  <div className="flex gap-2">
                    {row.status === "requested" && <button type="button" onClick={() => act({ resource: "orders", id: row.id, action: "confirm" }, "Confirmed")} className="text-xs font-bold text-emerald-700">Confirm</button>}
                    {["requested", "external"].includes(row.status) && <button type="button" onClick={() => act({ resource: "orders", id: row.id, action: "cancel" }, "Cancelled")} className="text-xs font-bold text-rose-700">Cancel</button>}
                  </div>
                </div>
                <ul className="mt-2 text-xs text-slate-600 space-y-1">
                  {(row.items || []).map((item) => <li key={item.id}>{item.quantity} × {item.title} — NPR {item.line_total_npr}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
