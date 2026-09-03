import { useEffect, useState } from "react"
import { fallbackImageUrl } from "../../utils/imageUtils"

const FALLBACK_NEPAL_PHOTOS = [
  "/images/destinations/kathmandu/durbar-square.jpg",
  "/images/destinations/pokhara/fewatal.jpg",
  "/images/destinations/lumbini/garden.jpg",
  "/images/destinations/everest/base-camp.jpg",
  "/images/destinations/chitwan/safari.jpg",
  "/images/destinations/nagarkot/sunrise-view.jpg",
  "/images/destinations/bandipur/hilltop-village.jpg",
  "/images/destinations/ilam/tea-gardens.jpg",
  "/images/destinations/rara/alpine-lake.jpg",
  "/images/destinations/mustang/lo-manthang.jpg",
]

function getFallbackForTitle(title) {
  if (!title) return FALLBACK_NEPAL_PHOTOS[0]
  const t = title.toLowerCase()
  if (t.includes("lumbini") || t.includes("maya") || t.includes("buddha")) return "/images/destinations/lumbini/garden.jpg"
  if (t.includes("bharatpur") || t.includes("chitwan") || t.includes("safari") || t.includes("rhino")) return "/images/destinations/chitwan/safari.jpg"
  if (t.includes("pokhara") || t.includes("phewa") || t.includes("fewa") || t.includes("lakeside")) return "/images/destinations/pokhara/fewatal.jpg"
  if (t.includes("everest") || t.includes("khumbu") || t.includes("ebc") || t.includes("namche")) return "/images/destinations/everest/base-camp.jpg"
  if (t.includes("kathmandu") || t.includes("thamel") || t.includes("durbar") || t.includes("pashupati")) return "/images/destinations/kathmandu/durbar-square.jpg"
  if (t.includes("nagarkot")) return "/images/destinations/nagarkot/sunrise-view.jpg"
  if (t.includes("bandipur")) return "/images/destinations/bandipur/hilltop-village.jpg"
  if (t.includes("ilam") || t.includes("kanyam") || t.includes("tea")) return "/images/destinations/ilam/tea-gardens.jpg"
  if (t.includes("rara")) return "/images/destinations/rara/alpine-lake.jpg"
  if (t.includes("mustang") || t.includes("muktinath")) return "/images/destinations/mustang/lo-manthang.jpg"

  return fallbackImageUrl(title) || FALLBACK_NEPAL_PHOTOS[Math.abs(title.length) % FALLBACK_NEPAL_PHOTOS.length]
}

const PlaceholderImage = ({ className = "", title = "Nepal Attraction", src = null, alt = "", cropBox = null }) => {
  const [failed, setFailed] = useState(false)
  
  useEffect(() => setFailed(false), [src])

  const effectiveSrc = (!src || failed) ? getFallbackForTitle(title || alt) : src

  return (
    <img
      src={effectiveSrc}
      alt={alt || title || "Nepal Landmark"}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`object-cover ${className}`}
    />
  )
}

export default PlaceholderImage
