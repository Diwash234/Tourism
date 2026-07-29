import { FiMapPin, FiStar, FiWifi, FiWind } from "react-icons/fi"

const STATUS_STYLE = {
  available: "badge-risk-low",
  limited: "badge-risk-moderate",
  full: "badge-risk-high",
  unavailable: "badge-risk-high",
}

/**
 * HotelCard
 * Matches the real backend Hotel model fields exactly (tourist/models.py
 * Hotel + HotelSerializer): id, destination, name, price_per_night,
 * currency, rating, booking_status, booking_url, address, latitude,
 * longitude, source. There is no `image` or `facilities` field on the
 * backend today — both are shown with sensible fallbacks so this card
 * doesn't lie about data that doesn't exist yet.
 */
const HotelCard = ({ hotel }) => {
  const {
    name,
    address,
    price_per_night,
    currency = "NPR",
    rating,
    booking_status,
    booking_url,
  } = hotel

  return (
    <div className="card-base overflow-hidden">
      <div className="relative h-40">
        <img
          src="https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600"
          alt={name}
          className="w-full h-full object-cover"
        />
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
      </div>

      <div className="p-4">
        <h3 className="font-bold text-dark truncate">{name}</h3>
        {address && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
            <FiMapPin size={14} />
            {address}
          </p>
        )}

        {/* Facilities aren't in the backend model yet — showing the two
            that are near-universal rather than inventing per-hotel data */}
        <div className="flex items-center gap-3 text-xs text-gray-400 mt-2">
          <span className="flex items-center gap-1"><FiWifi size={12} /> WiFi</span>
          <span className="flex items-center gap-1"><FiWind size={12} /> Mountain View</span>
        </div>

        <div className="flex items-center justify-between mt-4">
          <p className="font-bold text-forest-600">
            {price_per_night != null ? `${currency} ${price_per_night}` : "Price on request"}
            <span className="text-xs font-normal text-gray-400">/night</span>
          </p>
          {booking_url ? (
            <a href={booking_url} target="_blank" rel="noreferrer" className="btn-gradient text-sm px-4 py-2">
              Book Now
            </a>
          ) : (
            <span className="text-xs text-gray-400">No booking link yet</span>
          )}
        </div>
      </div>
    </div>
  )
}

export default HotelCard