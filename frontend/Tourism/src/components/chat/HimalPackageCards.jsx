import { Link } from "react-router-dom"
import { addToTripBasket } from "../../utils/tripBasket"

export default function HimalPackageCards({ offers, onAdd }) {
  if (!offers?.length) return null

  const add = (offer) => {
    addToTripBasket(offer)
    onAdd?.(offer)
  }

  return (
    <div className="max-w-[85%] mt-3 w-full space-y-2" data-testid="himal-package-cards">
      <p className="text-[11px] font-bold text-amber-900">
        Live packages (request to book — no card numbers here):
      </p>
      {offers.map((offer) => (
        <div
          key={offer.id || offer.slug}
          data-testid="himal-package-card"
          data-package-slug={offer.slug || ""}
          data-alternative={offer.is_alternative ? "true" : "false"}
          className="rounded-xl border border-amber-200 bg-white p-3 space-y-2"
        >
          <p className="text-[10px] font-black uppercase text-amber-800">
            {offer.kind} · {offer.duration_days || 1} day(s)
            {offer.is_alternative ? " · alternative" : ""}
          </p>
          {offer.is_alternative && (
            <p data-testid="himal-package-alternative" className="text-[10px] text-amber-800">
              Nearby-duration published alternative (not an exact match)
            </p>
          )}
          <p className="font-bold text-slate-900 text-sm">{offer.title}</p>
          <p className="text-xs text-slate-500">
            {offer.partner_name} · NPR {Number(offer.price_npr).toLocaleString()}
          </p>
          <div className="flex gap-2">
            <Link
              to={`/packages/${offer.slug}`}
              data-testid="himal-package-view"
              className="flex-1 text-center text-[11px] font-black rounded-lg bg-amber-400 text-gray-950 py-1.5"
            >
              View
            </Link>
            <button
              type="button"
              data-testid="himal-package-add"
              onClick={() => add(offer)}
              className="flex-1 text-[11px] font-black rounded-lg bg-emerald-700 text-white py-1.5"
            >
              Add to trip
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
