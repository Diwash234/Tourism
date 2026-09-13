/**
 * imageProviders.js
 *
 * WHY THIS EXISTS:
 * The backend already has a solid multi-source image pipeline
 * (Tourism/tourist/image_pipeline.py + utils.ensure_cover_photo) for
 * Destinations, but:
 *   1. It only ever runs lazily and needs `manage.py backfill_destination_images`
 *      to actually be run against every destination.
 *   2. Hotels have NO image field/pipeline on the backend at all
 *      (see HotelCard.jsx's own comment: "no image/images field exists
 *      on the backend today").
 * So even with real Unsplash/Wikimedia keys sitting in a `.env` file,
 * a lot of cards were always going to show a generic gradient, because
 * nothing was ever fetching a real photo for them client-side.
 *
 * This module is a lightweight, read-only, client-side fallback that
 * mirrors the backend's SOURCE_CHAIN exactly (image_pipeline.py):
 * Unsplash -> Pexels -> Pixabay -> Openverse -> Wikimedia, run in
 * parallel here (rather than backend's stop-at-first-hit) so a gallery
 * can show several *different* verified photos, not the same one
 * repeated. It never replaces a real backend image -- see SmartImage.jsx
 * and DestinationGallery.jsx, both of which only ever call this when
 * the backend genuinely has nothing (cover_image_url is null/empty),
 * confirmed against DestinationListSerializer.get_cover_image_url()
 * which returns None (not "") when there's no real photo -- so a
 * destination that already has a correct backend photo is never
 * touched by this file.
 *
 * SETUP:
 * Add to frontend/Tourism/.env (NOT .env.example, that's just a
 * template) — note the VITE_ prefix, which is REQUIRED. Vite only
 * exposes env vars prefixed with VITE_ to browser code; without the
 * prefix, import.meta.env.WHATEVER is always undefined at runtime.
 *
 *   VITE_UNSPLASH_ACCESS_KEY=your_real_unsplash_access_key
 *   VITE_PEXELS_API_KEY=your_real_pexels_api_key       (optional)
 *   VITE_PIXABAY_API_KEY=your_real_pixabay_api_key     (optional)
 *
 * Pexels/Pixabay are both free to sign up for and raise the odds of a
 * relevant hit considerably for smaller or less-photographed places.
 * Openverse and Wikimedia Commons need no key at all and work out of
 * the box, so this module never returns nothing just because a key is
 * missing -- it just skips that one source.
 */

const UNSPLASH_ACCESS_KEY = import.meta.env.VITE_UNSPLASH_ACCESS_KEY || ""
const PEXELS_API_KEY = import.meta.env.VITE_PEXELS_API_KEY || ""
const PIXABAY_API_KEY = import.meta.env.VITE_PIXABAY_API_KEY || ""
const WIKIMEDIA_API_URL =
  import.meta.env.VITE_WIKIMEDIA_API_URL || "https://commons.wikimedia.org/w/api.php"

// Same rejection list as the backend pipeline (tourist/image_pipeline.py)
// so a place-name search can't surface an unrelated portrait/selfie/
// stock-model photo just because it text-matched.
const REJECT_KEYWORDS = [
  "portrait", "selfie", "headshot", "model", "fashion", "makeup",
  "wedding dress", "studio shoot", "person smiling", "close-up of face",
]

function looksLikeAPlace(text, query) {
  const lower = (text || "").toLowerCase()
  if (REJECT_KEYWORDS.some((bad) => lower.includes(bad))) return false
  const queryWords = query.toLowerCase().split(/\s+/).filter((w) => w.length > 3)
  if (queryWords.length && !queryWords.some((w) => lower.includes(w))) return false
  return true
}

// In-memory cache so switching pages / re-rendering a list doesn't
// re-fire the same network request. Cleared on full page reload only.
const cache = new Map()

async function fetchUnsplash(query, { orientation = "landscape", count = 4 } = {}) {
  if (!UNSPLASH_ACCESS_KEY) return []
  try {
    const params = new URLSearchParams({
      query,
      per_page: String(Math.max(count, 3)),
      orientation, // "landscape" | "portrait" | "squarish"
    })
    const res = await fetch(`https://api.unsplash.com/search/photos?${params}`, {
      headers: { Authorization: `Client-ID ${UNSPLASH_ACCESS_KEY}` },
    })
    if (!res.ok) return []
    const data = await res.json()
    return (data.results || [])
      .filter((r) => looksLikeAPlace(`${r.description || ""} ${r.alt_description || ""}`, query))
      .map((r) => ({
        url: r.urls.regular,
        thumbnailUrl: r.urls.small,
        width: r.width,
        height: r.height,
        attribution: `Photo by ${r.user?.name || "Unsplash contributor"} on Unsplash`,
        sourceLink: r.links?.html,
        source: "unsplash",
      }))
  } catch {
    return []
  }
}

async function fetchPexels(query, { count = 4 } = {}) {
  if (!PEXELS_API_KEY) return []
  try {
    const params = new URLSearchParams({ query, per_page: String(Math.max(count, 3)) })
    const res = await fetch(`https://api.pexels.com/v1/search?${params}`, {
      headers: { Authorization: PEXELS_API_KEY },
    })
    if (!res.ok) return []
    const data = await res.json()
    return (data.photos || [])
      .filter((p) => looksLikeAPlace(p.alt || "", query))
      .map((p) => ({
        url: p.src.large,
        thumbnailUrl: p.src.medium,
        width: p.width,
        height: p.height,
        attribution: `Photo by ${p.photographer} on Pexels`,
        sourceLink: p.url,
        source: "pexels",
      }))
  } catch {
    return []
  }
}

async function fetchPixabay(query, { count = 4 } = {}) {
  if (!PIXABAY_API_KEY) return []
  try {
    const params = new URLSearchParams({
      key: PIXABAY_API_KEY,
      q: query,
      image_type: "photo",
      per_page: String(Math.max(count, 3)),
    })
    const res = await fetch(`https://pixabay.com/api/?${params}`)
    if (!res.ok) return []
    const data = await res.json()
    return (data.hits || [])
      .filter((h) => looksLikeAPlace(h.tags || "", query))
      .map((h) => ({
        url: h.largeImageURL,
        thumbnailUrl: h.webformatURL,
        width: h.imageWidth,
        height: h.imageHeight,
        attribution: `Photo by ${h.user} on Pixabay`,
        sourceLink: h.pageURL,
        source: "pixabay",
      }))
  } catch {
    return []
  }
}

async function fetchOpenverse(query, { count = 4 } = {}) {
  // No API key required -- CC-licensed image search, free to use.
  try {
    const params = new URLSearchParams({
      q: query,
      page_size: String(Math.max(count, 3)),
      license_type: "commercial,modification",
    })
    const res = await fetch(`https://api.openverse.org/v1/images/?${params}`)
    if (!res.ok) return []
    const data = await res.json()
    return (data.results || [])
      .filter((r) => looksLikeAPlace(r.title || "", query))
      .map((r) => ({
        url: r.url,
        thumbnailUrl: r.thumbnail || r.url,
        width: r.width,
        height: r.height,
        attribution: `${r.title || "Image"} by ${r.creator || "Unknown"} (${(r.license || "").toUpperCase()}, via Openverse)`,
        sourceLink: r.foreign_landing_url || r.url,
        source: "openverse",
      }))
  } catch {
    return []
  }
}

async function fetchWikimedia(query, { count = 4 } = {}) {
  try {
    const searchParams = new URLSearchParams({
      action: "query",
      list: "search",
      srsearch: `${query} filetype:bitmap`,
      srnamespace: "6",
      srlimit: String(Math.max(count * 2, 6)),
      format: "json",
      origin: "*", // required for anonymous cross-origin calls from a browser
    })
    const searchRes = await fetch(`${WIKIMEDIA_API_URL}?${searchParams}`)
    if (!searchRes.ok) return []
    const searchData = await searchRes.json()
    const hits = (searchData.query?.search || []).filter((hit) =>
      looksLikeAPlace(hit.title, query)
    )

    const results = []
    for (const hit of hits) {
      if (results.length >= count) break
      const infoParams = new URLSearchParams({
        action: "query",
        titles: hit.title,
        prop: "imageinfo",
        iiprop: "url|extmetadata|size",
        format: "json",
        origin: "*",
      })
      try {
        const infoRes = await fetch(`${WIKIMEDIA_API_URL}?${infoParams}`)
        if (!infoRes.ok) continue
        const infoData = await infoRes.json()
        const page = Object.values(infoData.query?.pages || {})[0]
        const imageInfo = page?.imageinfo?.[0]
        if (imageInfo?.url) {
          const artist = imageInfo.extmetadata?.Artist?.value?.replace(/<[^>]+>/g, "") || "Wikimedia Commons contributor"
          results.push({
            url: imageInfo.url,
            thumbnailUrl: imageInfo.url,
            width: imageInfo.width,
            height: imageInfo.height,
            attribution: `Photo: ${artist} (Wikimedia Commons)`,
            sourceLink: `https://commons.wikimedia.org/wiki/${encodeURIComponent(hit.title)}`,
            source: "wikimedia",
          })
        }
      } catch {
        // skip this one file, keep trying the rest
      }
    }
    return results
  } catch {
    return []
  }
}

/**
 * resolvePlaceImages
 * The single entry point everything else should call. Returns a
 * de-duplicated array of verified place photos (never throws, never
 * returns a generic filler — an empty array means "nothing relevant
 * found", and the caller decides its own placeholder policy, same
 * contract as the backend's resolve_place_image()).
 *
 * Queries all 5 sources in parallel and merges them in the same
 * priority order the backend uses (Unsplash, Pexels, Pixabay,
 * Openverse, Wikimedia) so a gallery gets a *mix* of photos rather
 * than 6 copies from a single source.
 *
 * @param {string} name - place name, e.g. "Phewa Lake"
 * @param {object} opts
 * @param {string} opts.context - biases the search, defaults to "Nepal"
 * @param {"landscape"|"portrait"} opts.orientation
 * @param {number} opts.count - how many images to return (default 4)
 */
export async function resolvePlaceImages(name, opts = {}) {
  const { context = "Nepal", orientation = "landscape", count = 4 } = opts
  if (!name) return []

  const cacheKey = `${name}|${context}|${orientation}|${count}`
  if (cache.has(cacheKey)) return cache.get(cacheKey)

  const query = `${name} ${context}`.trim()
  const promise = (async () => {
    const [unsplashResults, pexelsResults, pixabayResults, openverseResults, wikimediaResults] =
      await Promise.all([
        fetchUnsplash(query, { orientation, count }),
        fetchPexels(query, { count }),
        fetchPixabay(query, { count }),
        fetchOpenverse(query, { count }),
        fetchWikimedia(query, { count }),
      ])
    const merged = [...unsplashResults, ...pexelsResults, ...pixabayResults, ...openverseResults, ...wikimediaResults]
    const seen = new Set()
    const deduped = merged.filter((img) => {
      if (seen.has(img.url)) return false
      seen.add(img.url)
      return true
    })
    return deduped.slice(0, count)
  })()

  cache.set(cacheKey, promise)
  const result = await promise
  cache.set(cacheKey, result) // replace the pending promise with the resolved value
  return result
}

export default resolvePlaceImages