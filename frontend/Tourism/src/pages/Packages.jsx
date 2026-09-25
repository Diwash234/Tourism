import { useEffect, useMemo, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { FiCheck, FiMapPin, FiPackage, FiShoppingBag } from "react-icons/fi"
import EmptyState from "../components/common/EmptyState"
import ErrorState from "../components/ui/ErrorState"
import SkeletonLoader from "../components/common/SkeletonLoader"
import PlaceholderImage from "../components/common/PlaceholderImage"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSIntro from "../components/cms/CMSIntro"
import { addToTripBasket, getTripBasket } from "../utils/tripBasket"

const KINDS = [
  ["", "All offers"],
  ["package", "Packages"],
  ["hotel", "Stays"],
  ["tour", "Tours"],
  ["activity", "Activities"],
  ["restaurant", "Restaurants"],
  ["transfer", "Transfers"],
  ["guide", "Guides"],
  ["ad", "Sponsored"],
]

const Packages = () => {
  const { block: cmsBlock } = usePublicConfig().pageCMS("packages", ["intro", "page-intro"])
  const { showToast } = useToast()
  const [kind, setKind] = useState("")
  const [query, setQuery] = useState("")
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [basketCount, setBasketCount] = useState(getTripBasket().length)

  const requestSequence = useRef(0)
  const load = async (overrides = {}) => {
    const currentRequest = ++requestSequence.current
    setLoading(true)
    setLoadError("")
    try {
      const nextKind = overrides.kind ?? kind
      const nextQuery = overrides.query ?? query
      const { data } = await userApi.getMarketplaceListings({ kind: nextKind, q: nextQuery })
      if (currentRequest !== requestSequence.current) return
      setListings(Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [])
    } catch {
      if (currentRequest !== requestSequence.current) return
      setListings([])
      setLoadError("We couldn't load packages from the live catalogue right now.")
      showToast("Could not load packages from the live catalogue", "error")
    } finally {
      if (currentRequest === requestSequence.current) setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
    // Search text is intentionally submitted, not fetched on each keystroke.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind])

  const featured = useMemo(() => listings.filter((row) => row.is_featured), [listings])
  const standardListings = useMemo(() => listings.filter((row) => !row.is_featured), [listings])

  const add = (listing) => {
    const next = addToTripBasket(listing)
    setBasketCount(next.length)
    showToast(`${listing.title} added to your trip basket`, "success")
  }

  return (
    <div className="ny-page container-app py-10" data-testid="packages-page">
      <CMSIntro section={cmsBlock("intro")} />
      <PageHeader
        title="Travel Packages"
        subtitle="Live offers from approved hotels, operators and guides. Add what you need to a trip, then request to book — we never take card numbers here."
        icon={FiPackage}
        actions={
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
            <Link to="/collaborate" className="ny-btn ny-btn-secondary w-full justify-center sm:w-auto">List your hotel or tour</Link>
            <Link to="/checkout" className="ny-btn ny-btn-primary w-full justify-center sm:w-auto">
              <FiShoppingBag aria-hidden="true" /> Trip basket ({basketCount})
            </Link>
          </div>
        }
      />

      <form className="flex flex-col sm:flex-row gap-3 mb-6" onSubmit={(event) => { event.preventDefault(); load() }}>
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <label htmlFor="package-search" className="sr-only">Search packages and stays</label>
           <input id="package-search" className="input-field pl-11" placeholder="Search Pokhara, treks, stays…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <label htmlFor="package-kind" className="sr-only">Offer type</label>
         <select id="package-kind" className="input-field sm:w-48" value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map(([id, label]) => <option key={id || "all"} value={id}>{label}</option>)}
        </select>
        <button type="submit" className="btn-primary">Search</button>
      </form>

      {loading && <SkeletonLoader count={6} />}
      {!loading && loadError && <ErrorState title="Could not load packages" message={loadError} onRetry={load} />}
      {!loading && !loadError && listings.length === 0 && <EmptyState title={query.trim() || kind ? "No matching offers" : "No published packages yet"} subtitle={query.trim() || kind ? "Try a different search or clear the offer type filter." : "There are no published offers in the live catalogue. Approved hotels, operators and guides can collaborate to add one."} action={query.trim() || kind ? <button type="button" onClick={() => { setQuery(""); setKind(""); load({ kind: "", query: "" }) }} className="ny-btn ny-btn-secondary">Clear search</button> : <Link to="/collaborate" className="ny-btn ny-btn-secondary">List your service</Link>} />}

      {featured.length > 0 && (
        <section className="mb-8">
          <h2 className="section-title">Featured this season</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {featured.map((row) => <OfferCard key={`f-${row.id}`} listing={row} onAdd={add} featured />)}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
        {standardListings.map((row) => <OfferCard key={row.id} listing={row} onAdd={add} />)}
      </div>
    </div>
  )
}

function OfferCard({ listing, onAdd, featured }) {
  return (
    <article className="card-base overflow-hidden flex flex-col" data-testid="package-card" data-package-slug={listing.slug}>
      <div className="relative aspect-[16/9] w-full overflow-hidden bg-[var(--ny-soft-green)]">
        <PlaceholderImage src={listing.image_url} title={listing.title} alt={listing.title} className="h-full w-full" />
        <span className="absolute top-3 left-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-black uppercase text-emerald-900">{listing.kind}</span>
        {featured && <span className="absolute top-3 right-3 rounded-full bg-amber-400 px-2 py-0.5 text-[10px] font-black uppercase text-gray-950">Featured</span>}
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <p className="text-xs text-slate-500">{listing.partner_name || "Provider not recorded"} · {listing.city || listing.destination_name || "Location unavailable"}</p>
        <h3 className="text-lg font-black text-slate-900 mt-1">{listing.title}</h3>
        <p className="text-sm text-slate-600 mt-2 line-clamp-3">{listing.summary || listing.description}</p>
        <ul className="mt-3 space-y-1 text-xs text-slate-600">
          <li className="flex gap-2"><FiCheck className="text-emerald-600 mt-0.5" /> {listing.duration_days != null ? `${listing.duration_days} day${listing.duration_days === 1 ? "" : "s"}` : "Duration unavailable"}</li>
          {listing.includes && <li className="flex gap-2"><FiCheck className="text-emerald-600 mt-0.5" /> {listing.includes.split("\n")[0]}</li>}
        </ul>
        <p className="mt-4 text-2xl font-black text-slate-900">{listing.price_npr != null ? `${listing.currency || "NPR"} ${Number(listing.price_npr).toLocaleString()}` : "Price unavailable"}</p>
        <div className="mt-auto flex flex-col gap-2 pt-4 sm:flex-row">
          <Link to={`/packages/${listing.slug}`} className="ny-btn ny-btn-secondary flex-1 justify-center" aria-label={`View details for ${listing.title}`}>Details</Link>
          <button type="button" data-testid="add-to-trip" onClick={() => onAdd(listing)} className="ny-btn ny-btn-primary flex-1 justify-center" aria-label={`Add ${listing.title} to your trip`}>Add to trip</button>
        </div>
      </div>
    </article>
  )
}

export default Packages
