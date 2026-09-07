import { useEffect, useMemo, useState } from "react"
import PlaceholderImage from "../common/PlaceholderImage"
import { getDestinationImageUrl } from "../../utils/imageUtils"

/** Resilient hotel media chain: hotel-specific -> contextual destination -> explicit unavailable. */
export default function HotelMedia({ hotel, className = "", alt, showContextLabel = true }) {
  const candidates = useMemo(() => {
    const contextualLocal = getDestinationImageUrl({
      name: hotel.destination_name || hotel.destinationName || "",
      slug: hotel.destination_slug,
    })
    return [hotel.cover_image, hotel.external_image_url, hotel.image_url,
      hotel.destination_context_image_url, contextualLocal]
      .filter((value, index, all) => value && all.indexOf(value) === index)
  }, [hotel.cover_image, hotel.external_image_url, hotel.image_url, hotel.destination_context_image_url, hotel.destination_name, hotel.destinationName, hotel.destination_slug])
  const [index, setIndex] = useState(0)
  useEffect(() => setIndex(0), [candidates.join("|")])
  const src = candidates[index]
  if (!src) return <PlaceholderImage className={className} title={hotel.name || "hotel"}/>
  return <div className={`relative ${className}`}>
    <img src={src} alt={alt || hotel.name || "Hotel"} loading="lazy"
      onError={() => setIndex(current => current + 1)} className="w-full h-full object-cover"/>
    {showContextLabel && !hotel.image_is_hotel_specific && <span className="absolute bottom-2 right-2 rounded bg-black/65 px-2 py-1 text-[10px] font-bold text-white">Destination area photo</span>}
  </div>
}
