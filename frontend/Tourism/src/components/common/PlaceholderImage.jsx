import { useEffect, useRef, useState } from "react"
import { FiImage } from "react-icons/fi"
import { fallbackImageUrl } from "../../utils/imageUtils"
import { resolvePlaceImages } from "../../utils/imageProviders"

// Fallback labels, not place names — searching these would surface unrelated
// stock photos, which the conservative image policy forbids.
const GENERIC_LABELS = new Set([
  "Nepal Attraction",
  "Nepal Landmark",
  "Image unavailable",
  "Destination",
  "destination",
  "hotel",
])

function getFallbackForTitle(title) {
  if (!title) return ""
  return fallbackImageUrl(title) || ""
}

function searchableName(title, alt) {
  const name = title || alt || ""
  if (!name || GENERIC_LABELS.has(name)) return ""
  return name
}

// labelPlacement="top": for full-bleed background images with text laid over
// the bottom (hero / editorial tiles) -- keeps the honest "Image unavailable"
// tag out of the way of the overlaid title instead of centring it beneath.
const PlaceholderImage = ({ className = "", title = "Nepal Attraction", src = null, alt = "", labelPlacement = "center" }) => {
  const [brokenSrc, setBrokenSrc] = useState("")
  const [remote, setRemote] = useState(null) // { name, url, attribution, done }
  // The name whose lookup was last started. Kept in a ref (not state) so a
  // settling promise can never re-trigger the effect or race a newer lookup:
  // a stale result is dropped unless its name is still the requested one.
  const requestedFor = useRef("")

  useEffect(() => {
    const timer = setTimeout(() => setBrokenSrc(""), 0)
    return () => clearTimeout(timer)
  }, [src])

  const name = searchableName(title, alt)

  // Last resort: no usable card source AND no local landmark match, so the
  // card would otherwise show "Image unavailable" — do one best-effort,
  // keyless search (Wikimedia/Openverse, reject-keyword filtered) for the
  // place name. It only ever fires when there is currently NO image at all,
  // so the "never substitute an unrelated photo for a real one" policy in
  // imageUtils.js stands. resolvePlaceImages caches by name, so re-renders
  // and repeated cards never re-query.
  useEffect(() => {
    const cardSrc = src && brokenSrc !== src ? src : ""
    if (cardSrc) return
    if (getFallbackForTitle(title || alt)) return
    if (!name) return
    if (requestedFor.current === name) return
    requestedFor.current = name
    resolvePlaceImages(name, { count: 1 })
      .then((images) => {
        if (requestedFor.current !== name) return // superseded by a newer lookup
        const hit = Array.isArray(images) && images.length ? images[0] : null
        setRemote({ name, url: hit?.url || "", attribution: hit?.attribution || "", done: true })
      })
      .catch(() => {
        if (requestedFor.current !== name) return
        setRemote({ name, url: "", attribution: "", done: true })
      })
    // No synchronous setState here (react-hooks/set-state-in-effect): a null
    // `remote` already renders as "lookup pending", and `requestedFor`
    // dedupes the request without needing a state write.
  }, [src, brokenSrc, title, alt, name])

  const cardSrc = src && brokenSrc !== src ? src : ""
  const localSrc = cardSrc ? "" : getFallbackForTitle(title || alt)
  const remoteUrl = remote && remote.done && remote.name === name && brokenSrc !== remote.url ? remote.url : ""
  const effectiveSrc = cardSrc || localSrc || remoteUrl
  const searching = !effectiveSrc && Boolean(name) && !(remote && remote.name === name && remote.done)

  if (!effectiveSrc) {
    if (searching) {
      // Keep the reserved soft-green tile while the lookup runs instead of
      // flashing "Image unavailable" for a photo that is about to arrive.
      return (
        <div className={`flex items-center justify-center bg-[var(--ny-soft-green)] text-[var(--ny-green)] ${className}`} role="img" aria-label={alt || `${title || "Destination"} image loading`}>
          <span className="flex flex-col items-center gap-2 px-4 text-center opacity-50"><FiImage size={26} aria-hidden="true" /><span className="text-xs font-semibold">Finding photo…</span></span>
        </div>
      )
    }
    if (labelPlacement === "top") {
      return (
        <div className={`flex items-start justify-end bg-[var(--ny-green-dark)] p-3 ${className}`} role="img" aria-label={alt || `${title || "Destination"} image unavailable`}>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-black/35 px-2.5 py-1 text-xs font-semibold text-white/85"><FiImage size={13} aria-hidden="true" />Image unavailable</span>
        </div>
      )
    }
    return (
      <div className={`flex items-center justify-center bg-[var(--ny-soft-green)] text-[var(--ny-green)] ${className}`} role="img" aria-label={alt || `${title || "Destination"} image unavailable`}>
        <span className="flex flex-col items-center gap-2 px-4 text-center"><FiImage size={26} aria-hidden="true" /><span className="text-xs font-semibold">Image unavailable</span></span>
      </div>
    )
  }

  return (
    <img
      src={effectiveSrc}
      alt={alt || title || "Nepal Landmark"}
      loading="lazy"
      onError={() => setBrokenSrc(effectiveSrc)}
      title={effectiveSrc === remoteUrl ? remote?.attribution || undefined : undefined}
      className={`object-cover ${className}`}
    />
  )
}

export default PlaceholderImage
