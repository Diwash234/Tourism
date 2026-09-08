import { useEffect, useState } from "react"
import PlaceholderImage from "./PlaceholderImage"
import { resolvePlaceImages } from "../../utils/imageProviders"

// See SmartImage.jsx for why only Wikimedia gets a "verified" style
// label -- stock-photo sources (Unsplash/Pexels/Pixabay/Openverse)
// are keyword-matched, not location-verified, so they're labeled
// honestly as representative rather than implying precision they
// don't have.
const SOURCE_LABELS = {
  wikimedia: "Wikimedia",
  unsplash: "Representative photo",
  pexels: "Representative photo",
  pixabay: "Representative photo",
  openverse: "Representative photo",
}

/**
 * ImageGallery
 * Shows up to `count` images for a place: real backend gallery images
 * first, then live-fetched Unsplash/Wikimedia photos to fill any gap
 * up to `count`. Renders as a responsive CSS-columns masonry so mixed
 * landscape + portrait photos both look intentional instead of being
 * cropped into identical tiles.
 *
 * Props:
 *  - images: array of backend image urls (or objects with .image /
 *    .external_url / .display_url) - optional
 *  - name: place name, used as the search query to fetch extra photos
 *  - context: search bias, defaults to "Nepal"
 *  - count: total images to show, default 6
 *  - seed: for the placeholder gradient if nothing is found at all
 */
const toUrl = (item) =>
  typeof item === "string" ? item : item?.image || item?.external_url || item?.display_url || null

const ImageGallery = ({ images = [], name, context = "Nepal", count = 6, seed = 0 }) => {
  const backendUrls = images.map(toUrl).filter(Boolean)
  const [extra, setExtra] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    let cancelled = false
    const needed = count - backendUrls.length
    if (needed <= 0 || !name) {
      setLoaded(true)
      return
    }
    resolvePlaceImages(name, { context, orientation: "landscape", count: needed })
      .then((results) => {
        if (!cancelled) {
          setExtra(results)
          setLoaded(true)
        }
      })
      .catch(() => {
        if (!cancelled) setLoaded(true)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name, context, count, backendUrls.length])

  const allImages = [
    ...backendUrls.map((url) => ({ url, source: "backend" })),
    ...extra,
  ].slice(0, count)

  if (allImages.length === 0) {
    if (!loaded) {
      return (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton rounded-xl aspect-[4/3]" />
          ))}
        </div>
      )
    }
    return <PlaceholderImage seed={seed} className="w-full h-64 rounded-xl" />
  }

  return (
    <div className="columns-2 sm:columns-3 gap-3 [column-fill:_balance]">
      {allImages.map((img, i) => (
        <div key={img.url + i} className="relative mb-3 break-inside-avoid">
          <img
            src={img.url}
            alt={`${name || "Place"} photo ${i + 1}`}
            loading="lazy"
            className="w-full rounded-xl object-cover"
            onError={(e) => {
              e.currentTarget.parentElement.style.display = "none"
            }}
          />
          {img.source && img.source !== "backend" && (
            <span className="absolute bottom-1.5 right-1.5 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded leading-tight">
              {SOURCE_LABELS[img.source] || "Photo"}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}

export default ImageGallery