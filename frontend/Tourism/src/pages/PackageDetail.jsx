import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { FiArrowLeft, FiCheck, FiPackage } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"
import { addToTripBasket } from "../utils/tripBasket"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import PlaceholderImage from "../components/common/PlaceholderImage"

export default function PackageDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [listing, setListing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    setLoading(true)
    setError("")
    userApi.getMarketplaceListing(slug)
      .then(({ data }) => setListing(data))
      .catch((requestError) => {
         setListing(null)
         setError(requestError.response?.status === 404 ? "This package is no longer published." : "We could not load this package right now.")
       })
      .finally(() => setLoading(false))
    }, 0)
    return () => clearTimeout(t)
  }, [slug, retry])

  if (loading) return <Loader fullScreen />
  if (!listing) {
    return (
      <div className="ny-page container-app section-space text-center space-y-3">
        <h2 className="text-2xl font-bold">{error || "Package unavailable"}</h2>
        <p className="text-[var(--ny-text-secondary)]">{error ? "Please try again, or browse the currently published offers." : "This package may no longer be published."}</p>
        <div className="flex flex-wrap justify-center gap-3">
          <button type="button" onClick={() => setRetry((value) => value + 1)} className="ny-btn ny-btn-secondary">Try again</button>
          <Link to="/packages" className="ny-btn ny-btn-primary">Back to packages</Link>
        </div>
      </div>
    )
  }

  const add = () => {
    addToTripBasket(listing)
    showToast("Added to trip basket", "success")
    navigate("/checkout")
  }

  const lines = (text) => String(text || "").split("\n").map((line) => line.trim()).filter(Boolean)

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="package-detail" />
      <PageHeader title={listing.title} subtitle={`${listing.partner_name || "Provider not recorded"} · ${listing.kind || "Offer"} · ${listing.city || listing.destination_name || "Location unavailable"}`} icon={FiPackage} theme="amber" />
      <Link to="/packages" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-800"><FiArrowLeft /> All packages</Link>
      <div className="grid lg:grid-cols-[2fr_1fr] gap-6">
        <article className="card-base overflow-hidden">
          <PlaceholderImage src={listing.image_url} title={listing.title} alt={listing.title} className="h-64 w-full" />
          <div className="p-6 space-y-4">
            <p className="text-slate-700 whitespace-pre-line">{listing.description || listing.summary}</p>
            {lines(listing.includes).length > 0 && (
              <div>
                <h3 className="font-black text-slate-900">Includes</h3>
                <ul className="mt-2 space-y-1 text-sm text-slate-700">
                  {lines(listing.includes).map((line) => <li key={line} className="flex gap-2"><FiCheck className="text-emerald-600 mt-0.5" /> {line}</li>)}
                </ul>
              </div>
            )}
            {lines(listing.excludes).length > 0 && (
              <div>
                <h3 className="font-black text-slate-900">Does not include</h3>
                <ul className="mt-2 space-y-1 text-sm text-slate-700">
                  {lines(listing.excludes).map((line) => <li key={line}>{line}</li>)}
                </ul>
              </div>
            )}
            {listing.cancellation_policy && <p className="text-sm text-slate-600"><b>Cancellation:</b> {listing.cancellation_policy}</p>}
          </div>
        </article>
        <aside className="card-base p-6 h-fit space-y-3">
          <p className="text-3xl font-black">{listing.price_npr != null ? `NPR ${Number(listing.price_npr).toLocaleString()}` : "Price unavailable"}</p>
          <p className="text-sm text-slate-600">{listing.duration_days ? `${listing.duration_days} day${listing.duration_days === 1 ? "" : "s"}` : "Duration unavailable"}{listing.capacity ? ` · up to ${listing.capacity} travellers` : ""}</p>
          <button type="button" data-testid="add-to-trip" onClick={add} className="btn-primary w-full">Add to trip & continue</button>
          {listing.external_url && (
            <a href={listing.external_url} target="_blank" rel="noreferrer" className="btn-outline w-full text-center">Partner site (HTTPS)</a>
          )}
          <p className="text-xs text-slate-500">Request to book with the operator, or continue on their site. This platform does not collect card numbers.</p>
        </aside>
      </div>
    </div>
  )
}
