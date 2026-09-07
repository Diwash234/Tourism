import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { FiArrowLeft, FiCheck, FiPackage } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"
import { addToTripBasket } from "../utils/tripBasket"

export default function PackageDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [listing, setListing] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    userApi.getMarketplaceListing(slug)
      .then(({ data }) => setListing(data))
      .catch(() => setListing(null))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <Loader fullScreen />
  if (!listing) {
    return (
      <div className="container-app py-16 text-center space-y-3">
        <h2 className="text-2xl font-black">Offer not found</h2>
        <p className="text-slate-600">It may be unpublished. Browse live packages instead.</p>
        <Link to="/packages" className="btn-primary">Back to packages</Link>
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
    <div className="container-app py-10 space-y-6">
      <PageHeader title={listing.title} subtitle={`${listing.partner_name} · ${listing.kind} · ${listing.city || listing.destination_name || "Nepal"}`} icon={FiPackage} theme="amber" />
      <Link to="/packages" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-800"><FiArrowLeft /> All packages</Link>
      <div className="grid lg:grid-cols-[2fr_1fr] gap-6">
        <article className="card-base overflow-hidden">
          {listing.image_url && <img src={listing.image_url} alt="" className="w-full h-64 object-cover" />}
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
          <p className="text-3xl font-black">NPR {Number(listing.price_npr).toLocaleString()}</p>
          <p className="text-sm text-slate-600">{listing.duration_days} day{listing.duration_days === 1 ? "" : "s"} · up to {listing.capacity} travellers</p>
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
