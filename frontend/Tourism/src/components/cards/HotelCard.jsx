import { FiMapPin, FiStar, FiWifi, FiNavigation, FiImage, FiGlobe, FiPhoneCall } from "react-icons/fi"
import HotelMedia from "./HotelMedia"
import VerificationBadge from "../common/VerificationBadge"
import { useI18n } from "../../i18n"

const STATUS_STYLE = {
  available: "badge-risk-low",
  limited: "badge-risk-moderate",
  full: "badge-risk-high",
  unavailable: "badge-risk-high",
}

// Price is shown only when the API record provides it. The backend does not
// currently expose a verified price tier, so the UI does not infer one.

/* HotelCard
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
  const { t } = useI18n()
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
    facilities,
  } = hotel

  const gallery = Array.isArray(images) && images.length > 0 ? images : null

  return (
    <div className="card-base overflow-hidden">
      <div className="relative h-40">
        <HotelMedia hotel={{ ...hotel, image_url: gallery?.[0] || hotel.displayImage || hotel.image_url }} className="w-full h-full" />
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
          <span className={`absolute top-3 right-3 ${STATUS_STYLE[booking_status?.toLowerCase()] || "bg-slate-100 text-slate-600"}`}>
            {booking_status}
          </span>
        )}
        {hotel.amenities && (
          <span className={`absolute bottom-3 left-3 text-white text-xs font-semibold px-2.5 py-1 rounded-full bg-[var(--ny-green)]`}>
            {t("hotelcard.amenities_listed")}
          </span>
        )}
      </div>

      <div className="p-4">
        <h3 className="font-bold text-dark truncate">{name || t("hotelcard.name_unavailable")}</h3>
        <VerificationBadge record={hotel} className="mt-1.5" />
        {address && (
          <p className="text-sm text-gray-500 flex items-center gap-1 mt-1 min-w-0">
            <FiMapPin size={14} className="shrink-0" />
            <span className="truncate">{address}</span>
          </p>
        )}
        {destinationName && (
          <p className="text-xs text-himalaya-500 mt-1">{t("hotelcard.near", { name: destinationName })}</p>
        )}

        {Array.isArray(facilities) && facilities.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-gray-400 mt-2">
            {facilities.slice(0, 3).map((f) => (
              <span
                key={f}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-50 border border-gray-100 capitalize"
              >
                {String(f).toLowerCase() === "wifi" && <FiWifi size={11} />}
                {String(f).replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between mt-4 gap-2">
          <p className="font-bold text-forest-600">
            {price_per_night != null ? `${currency} ${price_per_night}` : t("hotelcard.price_on_request")}
            <span className="text-xs font-normal text-gray-400">{t("common.per_night")}</span>
          </p>
          <div className="flex items-center gap-1.5 shrink-0 flex-wrap justify-end">
            {latitude != null && longitude != null && (
              <a
                href={`https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`}
                target="_blank"
                rel="noreferrer"
                className="grid h-10 w-10 place-items-center rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] text-[var(--ny-green)] transition hover:bg-[#DDEFE7]"
                title={t("hotelcard.view_on_map")}
                aria-label={t("hotelcard.view_on_map_name", { name: name || t("hotelcard.name_unavailable") })}
              >
                <FiNavigation size={15} aria-hidden="true" />
              </a>
            )}
            {hotel.phone_number && <a href={`tel:${String(hotel.phone_number).replace(/[^0-9+]/g, "")}`} className="grid h-10 w-10 place-items-center rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] text-[var(--ny-green)] transition hover:bg-[#DDEFE7]" title={t("hotelcard.call_desk")} aria-label={t("hotelcard.call_name", { name: name || "" })}><FiPhoneCall size={15} aria-hidden="true" /></a>}
            {hotel.website_url && <a href={hotel.website_url} target="_blank" rel="noreferrer" className="ny-btn ny-btn-secondary min-h-10 px-3 text-xs" title={t("hotelcard.official_website")}><FiGlobe size={14} aria-hidden="true" />{t("hotelcard.web")}</a>}
            {booking_url && <a href={booking_url} target="_blank" rel="noreferrer" className="ny-btn ny-btn-primary min-h-10 px-3 text-xs">{t("hotelcard.view_booking")}</a>}
            {!hotel.phone_number && !hotel.website_url && !booking_url && <span className="text-xs text-[var(--ny-text-secondary)]">{t("hotelcard.booking_unavailable")}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default HotelCard