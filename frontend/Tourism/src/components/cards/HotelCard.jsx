import { FiMapPin, FiStar, FiWifi, FiWind, FiNavigation, FiImage, FiGlobe, FiPhoneCall } from "react-icons/fi"
import PlaceholderImage from "../common/PlaceholderImage"
import { getDestinationImageUrl, getHotelImageUrl } from "../../utils/imageUtils"

const STATUS_STYLE = {
  available: "badge-risk-low",
  limited: "badge-risk-moderate",
  full: "badge-risk-high",
  unavailable: "badge-risk-high",
}

// NEW: category color coding by price tier. Currency-aware because the
// real backend data mixes USD and NPR (Hotel.currency field) — a flat
// $30/$80 threshold would misclassify every NPR-priced hotel as
// "luxury". Thresholds are a reasonable approximation, not from any
// backend field (there's no tier field on the Hotel model).
function getPriceTier(price, currency) {
  if (price == null) return null
  const isNPR = (currency || "").toUpperCase() === "NPR"
  const [budgetMax, midMax] = isNPR ? [3000, 8000] : [30, 80]
  if (price <= budgetMax) return { label: "Budget", className: "bg-forest-500" }
  if (price <= midMax) return { label: "Mid-range", className: "bg-saffron-500" }
  return { label: "Luxury", className: "bg-himalaya-500" }
}

/**
 * HotelCard
 * Matches the real backend Hotel model fields (tourist/models.py Hotel +
 * HotelSerializer): id, destination, name, price_per_night, currency,
 * rating, booking_status, booking_url, address, latitude, longitude,
 * source. No `image`/`images`/`facilities` field exists on the backend
 * today — `hotel.images` is read defensively in case that's added
 * later, falling back to a single placeholder.
 *
 * destinationName is optional — pass it when the caller already knows
 * it (e.g. DestinationDetails.jsx, which fetches hotels nested under
 * the destination it's already showing). Standalone hotel-search pages
 * don't have it without an extra lookup per hotel, so it's omitted
 * there rather than faked.
 */
const HotelCard = ({ hotel, destinationName }) => {
  const {
    name,
    address,
    price_per_night,
    currency = "NPR",
    rating,
    booking_status,
    booking_url,
    latitude,
    longitude,
    images,
  } = hotel

  const tier = getPriceTier(price_per_night, currency)
  const gallery = Array.isArray(images) && images.length > 0 ? images : null

  return (
    <div className="card-base overflow-hidden">
      <div className="relative h-40">
        {gallery?.[0] || hotel.displayImage || hotel.image_url || hotel.image ? (
          <img
            src={gallery?.[0] || hotel.displayImage || hotel.image_url || hotel.image || getHotelImageUrl(hotel)}
            alt={name}
            onError={(e) => {
              // unique per-hotel postcard fallback — never a shared generic photo
              e.target.onerror = null;
              e.target.src = getHotelImageUrl(hotel);
            }}
            className="w-full h-full object-cover"
          />
        ) : (
          <img
            src={getHotelImageUrl(hotel)}
            alt={name}
            className="w-full h-full object-cover"
          />
        )}
        {gallery && gallery.length > 1 && (
          <span className="absolute bottom-3 right-3 flex items-center gap-1 bg-black/60 text-white text-xs px-2 py-1 rounded-full">
            <FiImage size={11} /> +{gallery.length - 1}
          </span>
        )}
        {rating != null && (
          <div className="absolute top-3 left-3 flex items-center gap-1 bg-white/95 px-2.5 py-1 rounded-full text-sm font-semibold text-saffron-600">
            <FiStar className="fill-saffron-500 text-saffron-500" size={14} />
            {rating}
          </div>
        )}
        {booking_status && (
          <span className={`absolute top-3 right-3 ${STATUS_STYLE[booking_status?.toLowerCase()] || "badge-risk-moderate"}`}>
            {booking_status}
          </span>
        )}
        {tier && (
          <span className={`absolute bottom-3 left-3 text-white text-xs font-semibold px-2.5 py-1 rounded-full ${tier.className}`}>
            {tier.label}
          </span>
        )}
      </div>

      <div className="p-4">
        <h3 className="font-bold text-dark truncate">{name}</h3>
        {address && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
            <FiMapPin size={14} />
            {address}
          </p>
        )}
        {destinationName && (
          <p className="text-xs text-himalaya-500 mt-1">Near {destinationName}</p>
        )}

        <div className="flex items-center gap-3 text-xs text-gray-400 mt-2">
          <span className="flex items-center gap-1"><FiWifi size={12} /> WiFi</span>
          <span className="flex items-center gap-1"><FiWind size={12} /> Mountain View</span>
        </div>

        <div className="flex items-center justify-between mt-4 gap-2">
          <p className="font-bold text-forest-600">
            {price_per_night != null ? `${currency} ${price_per_night}` : "Price on request"}
            <span className="text-xs font-normal text-gray-400">/night</span>
          </p>
          <div className="flex items-center gap-1.5 shrink-0 flex-wrap justify-end">
            {latitude && longitude && (
              <a
                href={`https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`}
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-600"
                title="View on map"
              >
                <FiNavigation size={14} />
              </a>
            )}
            <a
              href={`tel:${(hotel.phone_number || hotel.phone || "+977-61-520000").replace(/[^0-9+]/g, "")}`}
              className="px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center gap-1"
              title="Call Hotel Desk"
            >
              <FiPhoneCall size={12} />
            </a>
            <a
              href={hotel.website_url || hotel.website || "https://nepalhotels.com"}
              target="_blank"
              rel="noreferrer"
              className="px-2.5 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-900 text-xs font-bold flex items-center gap-1"
              title="Official Website"
            >
              <FiGlobe size={12} /> Web
            </a>
            <a
              href={booking_url || hotel.website_url || hotel.website || "https://booking.com"}
              target="_blank"
              rel="noreferrer"
              className="btn-gradient text-xs px-3 py-1.5 rounded-lg font-bold"
            >
              Book Now
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HotelCard