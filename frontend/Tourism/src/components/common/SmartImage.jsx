import { useEffect, useState } from "react"
import PlaceholderImage from "./PlaceholderImage"
import { resolvePlaceImages } from "../../utils/imageProviders"

/**
 * SmartImage
 *
 * Drop-in replacement for the old pattern:
 *   {cover_image_url ? <img src={cover_image_url} /> : <PlaceholderImage />}
 *
 * New behavior, additive on top of the old one:
 *   1. If `src` is given and loads fine -> render it, exactly as before.
 *   2. If `src` is missing, OR it 404s/fails to load -> live-fetch a real,
 *      verified photo for `name` from Unsplash/Wikimedia (client-side,
 *      see utils/imageProviders.js) and show that instead.
 *   3. Only if step 2 finds nothing does it fall back to the on-brand
 *      gradient PlaceholderImage, same as before.
 *
 * This is what actually fixes "hotels have no images" (backend has no
 * image field for hotels at all) and "destination photos are wrong/
 * missing" (backend pipeline hasn't been backfilled yet) without
 * waiting on any backend change.
 *
 * Props:
 *  - src: existing backend image url (optional)
 *  - name: place name used as the search query for the live fallback
 *  - context: search bias, defaults to "Nepal"
 *  - orientation: "landscape" | "portrait", defaults to "landscape"
 *  - seed: number/string used to pick a consistent placeholder gradient
 *  - alt, className: passed straight to the rendered <img>
 *  - showAttribution: show a tiny bottom-corner credit for live-fetched
 *    photos (Unsplash/Wikimedia require attribution) - default true
 */
// FIXED: labels used to just show the source brand ("Unsplash",
// "Pexels"...) as if that implied a verified photo of the exact
// place. It doesn't -- those are generic stock-photo keyword
// searches with no location verification, which produced real
// inaccurate matches for hyperlocal/obscure destination names
// (confirmed against the live database: stock search results for
// things like "Pame Picnic Site" or "balbalika picnic side" are
// generic Nepal-ish photos, not verified depictions of that exact
// spot). Wikimedia file titles are contributor-written descriptions
// of the actual photographed subject, a meaningfully stronger signal
// -- so only Wikimedia keeps a specific "verified" label; every stock
// source is labeled as a representative/generic match instead.
const SOURCE_LABELS = {
  wikimedia: "Wikimedia",
  unsplash: "Representative photo",
  pexels: "Representative photo",
  pixabay: "Representative photo",
  openverse: "Representative photo",
}

const SmartImage = ({
  src,
  name,
  context = "Nepal",
  orientation = "landscape",
  seed = 0,
  alt = "",
  className = "",
  showAttribution = true,
}) => {
  const [status, setStatus] = useState(src ? "backend" : "loading")
  const [fetchedImage, setFetchedImage] = useState(null)

  // Reset when the backend src actually changes (e.g. list re-fetch)
  useEffect(() => {
    setStatus(src ? "backend" : "loading")
    setFetchedImage(null)
  }, [src])

  useEffect(() => {
    let cancelled = false
    if (status !== "loading" || !name) {
      if (status === "loading" && !name) setStatus("placeholder")
      return
    }

    resolvePlaceImages(name, { context, orientation, count: 1 })
      .then((results) => {
        if (cancelled) return
        if (results.length > 0) {
          setFetchedImage(results[0])
          setStatus("fetched")
        } else {
          setStatus("placeholder")
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("placeholder")
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, name, context, orientation])

  if (status === "backend") {
    return (
      <img
        src={src}
        alt={alt}
        className={className}
        loading="lazy"
        onError={() => setStatus("loading")}
      />
    )
  }

  if (status === "fetched" && fetchedImage) {
    return (
      <div className="relative w-full h-full">
        <img
          src={fetchedImage.url}
          alt={alt}
          className={className}
          loading="lazy"
          onError={() => setStatus("placeholder")}
        />
        {showAttribution && (
          <span className="absolute bottom-1 right-1 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded leading-tight">
            {SOURCE_LABELS[fetchedImage.source] || "Photo"}
          </span>
        )}
      </div>
    )
  }

  if (status === "loading") {
    return <div className={`skeleton ${className}`} />
  }

  return <PlaceholderImage seed={seed} className={className} />
}

export default SmartImage