import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { FiCheck, FiMapPin, FiPackage, FiShoppingBag } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"
import { addToTripBasket, getTripBasket } from "../utils/tripBasket"

const KINDS = [
  ["", "All offers"],
  ["package", "Packages"],
  ["hotel", "Stays"],
  ["tour", "Tours"],
  ["activity", "Activities"],
  ["ad", "Sponsored"],
]

const Packages = () => {
  const { showToast } = useToast()
  const [kind, setKind] = useState("")
  const [query, setQuery] = useState("")
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [basketCount, setBasketCount] = useState(getTripBasket().length)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await userApi.getMarketplaceListings({ kind, q: query })
      setListings(data.results || [])
    } catch {
      setListings([])
      showToast("Could not load packages from the live catalogue", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [kind])

  const featured = useMemo(() => listings.filter((row) => row.is_featured), [listings])

  const add = (listing) => {
    const next = addToTripBasket(listing)
    setBasketCount(next.length)
    showToast(`${listing.title} added to your trip basket`, "success")
  }

  return (
    <div className="container-app py-10" data-testid="packages-page">
      <PageHeader
        title="Travel Packages"
        subtitle="Live offers from the admin desk and approved hotels, operators and guides. Add what you need to a trip, then request to book — we never take card numbers here."
        icon={FiPackage}
        theme="amber"
        actions={
          <div className="flex gap-2">
            <Link to="/collaborate" className="px-4 py-2 rounded-xl bg-white/15 text-white text-sm font-bold">List your hotel or tour</Link>
            <Link to="/checkout" className="px-4 py-2 rounded-xl bg-white text-amber-950 text-sm font-black flex items-center gap-2">
              <FiShoppingBag /> Trip basket ({basketCount})
            </Link>
          </div>
        }
      />

      <form className="flex flex-col sm:flex-row gap-3 mb-6" onSubmit={(event) => { event.preventDefault(); load() }}>
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="input-field pl-11" placeholder="Search Pokhara, treks, stays…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <select className="input-field sm:w-48" value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map(([id, label]) => <option key={id || "all"} value={id}>{label}</option>)}
        </select>
        <button type="submit" className="btn-primary">Search</button>
      </form>

      {loading && <p className="text-sm text-slate-600">Loading published offers…</p>}
      {!loading && listings.length === 0 && (
        <div className="card-base p-8 text-center">
          <p className="font-bold text-slate-900">No published packages yet</p>
          <p className="text-sm text-slate-600 mt-2">An administrator can add them from Admin → Packages & partners, or a hotel can apply to collaborate.</p>
        </div>
      )}

      {featured.length > 0 && (
        <section className="mb-8">
          <h2 className="section-title">Featured this season</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {featured.map((row) => <OfferCard key={`f-${row.id}`} listing={row} onAdd={add} featured />)}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {listings.map((row) => <OfferCard key={row.id} listing={row} onAdd={add} />)}
      </div>
    </div>
  )
}

function OfferCard({ listing, onAdd, featured }) {
  return (
    <article className="card-base overflow-hidden flex flex-col" data-testid="package-card" data-package-slug={listing.slug}>
      <div className="h-40 bg-emerald-900 relative">
        {listing.image_url ? (
          <img src={listing.image_url} alt={listing.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-emerald-800 to-amber-700" />
        )}
        <span className="absolute top-3 left-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-black uppercase text-emerald-900">{listing.kind}</span>
        {featured && <span className="absolute top-3 right-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-black uppercase text-gray-950">Featured</span>}
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <p className="text-xs text-slate-500">{listing.partner_name} · {listing.city || listing.destination_name || "Nepal"}</p>
        <h3 className="text-lg font-black text-slate-900 mt-1">{listing.title}</h3>
        <p className="text-sm text-slate-600 mt-2 line-clamp-3">{listing.summary || listing.description}</p>
        <ul className="mt-3 space-y-1 text-xs text-slate-600">
          <li className="flex gap-2"><FiCheck className="text-emerald-600 mt-0.5" /> {listing.duration_days} day{listing.duration_days === 1 ? "" : "s"}</li>
          {listing.includes && <li className="flex gap-2"><FiCheck className="text-emerald-600 mt-0.5" /> {listing.includes.split("\n")[0]}</li>}
        </ul>
        <p className="mt-4 text-2xl font-black text-slate-900">NPR {Number(listing.price_npr).toLocaleString()}</p>
        <div className="mt-4 flex gap-2">
          <Link to={`/packages/${listing.slug}`} className="flex-1 btn-outline text-center">Details</Link>
          <button type="button" data-testid="add-to-trip" onClick={() => onAdd(listing)} className="flex-1 btn-primary">Add to trip</button>
        </div>
      </div>
    </article>
  )
}

export default Packages
