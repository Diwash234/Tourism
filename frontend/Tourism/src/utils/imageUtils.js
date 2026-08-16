/**
 * frontend/Tourism/src/utils/imageUtils.js
 *
 * Central image resolver for the whole app.
 *
 * Design rules:
 *  1. Always prefer the image URL returned by the backend (cover_image_url /
 *     image_url / external_url), which now correctly resolves external
 *     Unsplash/Wikimedia URLs stored in the database instead of mangling
 *     them into broken "/media/https%3A/..." links.
 *  2. Never return solid colour blocks. The old bundled /images/destinations/*
 *     files were flat purple rectangles, so we no longer fall back to them.
 *  3. Provide a varied, category-aware set of REAL landscape photos as the
 *     last-resort fallback so cards never look identical.
 */

// A varied pool of openly-licensed (Unsplash License) landscape photos used
// only when the backend has no image at all. The pool is intentionally
// diverse so cards don't all show the same picture.
const FALLBACK_POOL = [
  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&q=80",
  "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80",
  "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80",
  "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&q=80",
  "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&q=80",
  "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80",
  "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80",
  "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80",
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80",
  "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80",
  "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1200&q=80",
  "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1200&q=80",
  "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80",
  "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80",
  "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&q=80",
  "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80",
]

/*
 * Real place-specific curated Nepal photos (generated AI JPEGs stored locally
 * under /images/destinations/<slug>/...). These are proper photographic images
 * (not colour blocks) used as the highest-priority fallback when the backend
 * has no usable cover_image_url for a destination.
 * Slug keys match lowercased destination names / common aliases.
 */
const LOCAL_NEPAL_PHOTOS = {
  // Nagarkot
  nagarkot:        "/images/destinations/nagarkot/sunrise-view.jpg",
  // Pokhara / Phewa
  pokhara:         "/images/destinations/pokhara/fewatal.jpg",
  phewa:           "/images/destinations/pokhara/fewatal.jpg",
  fewa:            "/images/destinations/pokhara/fewatal.jpg",
  "fewa tal":      "/images/destinations/pokhara/fewatal.jpg",
  "phewa lake":    "/images/destinations/pokhara/fewatal.jpg",
  "phewa tal":     "/images/destinations/pokhara/fewatal.jpg",
  // Everest / Khumbu
  everest:         "/images/destinations/everest/base-camp.jpg",
  "everest base camp": "/images/destinations/everest/base-camp.jpg",
  ebc:             "/images/destinations/everest/base-camp.jpg",
  khumbu:          "/images/destinations/everest/base-camp.jpg",
  sagarmatha:      "/images/destinations/everest/base-camp.jpg",
  // Kathmandu Valley
  kathmandu:       "/images/destinations/kathmandu/durbar-square.jpg",
  "kathmandu durbar": "/images/destinations/kathmandu/durbar-square.jpg",
  bhaktapur:       "/images/destinations/bhaktapur/durbar.jpg",
  patan:           "/images/destinations/patan/durbar.jpg",
  lalitpur:        "/images/destinations/patan/durbar.jpg",
  "patan durbar":  "/images/destinations/patan/durbar.jpg",
  "bhaktapur durbar": "/images/destinations/bhaktapur/durbar.jpg",
  // Chitwan
  chitwan:         "/images/destinations/chitwan/safari.jpg",
  "chitwan national park": "/images/destinations/chitwan/safari.jpg",
  // Lumbini
  lumbini:         "/images/destinations/lumbini/garden.jpg",
  // Annapurna
  annapurna:       "/images/destinations/annapurna/trek.jpg",
  "annapurna circuit": "/images/destinations/annapurna/trek.jpg",
  "annapurna base camp": "/images/destinations/annapurna/trek.jpg",
  abc:             "/images/destinations/annapurna/trek.jpg",
  // Mustang
  mustang:         "/images/destinations/mustang/lo-manthang.jpg",
  "upper mustang": "/images/destinations/mustang/lo-manthang.jpg",
  "lo manthang":   "/images/destinations/mustang/lo-manthang.jpg",
  "lower mustang": "/images/destinations/mustang/lo-manthang.jpg",
  // Ilam
  ilam:            "/images/destinations/ilam/tea-gardens.jpg",
  "ilam tea":      "/images/destinations/ilam/tea-gardens.jpg",
  kanyam:          "/images/destinations/ilam/tea-gardens.jpg",
  // Janakpur
  janakpur:        "/images/destinations/janakpur/janaki-mandir.jpg",
  "janaki mandir": "/images/destinations/janakpur/janaki-mandir.jpg",
  "janakpur dham": "/images/destinations/janakpur/janaki-mandir.jpg",
  // Bandipur
  bandipur:        "/images/destinations/bandipur/hilltop-village.jpg",
  // Bardiya
  bardiya:         "/images/destinations/bardiya/tiger-reserve.jpg",
  "bardiya national park": "/images/destinations/bardiya/tiger-reserve.jpg",
  "bardia":        "/images/destinations/bardiya/tiger-reserve.jpg",
  // Dolpo
  dolpo:           "/images/destinations/dolpo/highland-village.jpg",
  "upper dolpo":   "/images/destinations/dolpo/highland-village.jpg",
  "shey phoksundo":"/images/destinations/dolpo/highland-village.jpg",
  phoksundo:       "/images/destinations/dolpo/highland-village.jpg",
  // Gosaikunda
  gosaikunda:      "/images/destinations/gosaikunda/glacial-lake.jpg",
  "gosainkunda":   "/images/destinations/gosaikunda/glacial-lake.jpg",
  langtang:        "/images/destinations/gosaikunda/glacial-lake.jpg",
  // Koshi Tappu
  "koshi tappu":   "/images/destinations/koshi-tappu/wetlands.jpg",
  "kosi tappu":    "/images/destinations/koshi-tappu/wetlands.jpg",
  "koshi tuppu":   "/images/destinations/koshi-tappu/wetlands.jpg",
  // Manaslu
  manaslu:         "/images/destinations/manaslu/mountain-peak.jpg",
  "manaslu circuit":"/images/destinations/manaslu/mountain-peak.jpg",
  // Rara
  rara:            "/images/destinations/rara/alpine-lake.jpg",
  "rara lake":     "/images/destinations/rara/alpine-lake.jpg",
  "rara national park": "/images/destinations/rara/alpine-lake.jpg",
  // Tilicho
  tilicho:         "/images/destinations/tilicho/himalayan-lake.jpg",
  "tilicho lake":  "/images/destinations/tilicho/himalayan-lake.jpg",
}

const lookupLocalNepal = (name) => {
  if (!name) return null
  const n = String(name).toLowerCase().trim()
  if (LOCAL_NEPAL_PHOTOS[n]) return LOCAL_NEPAL_PHOTOS[n]
  // substring match (e.g. "Nagarkot Viewpoint" -> nagarkot)
  for (const key of Object.keys(LOCAL_NEPAL_PHOTOS)) {
    if (n.includes(key)) return LOCAL_NEPAL_PHOTOS[key]
  }
  return null
}

// Category-keyword -> fallback image (only used when no backend image exists)
const CATEGORY_FALLBACK = {
  mountain: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80",
  trek: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80",
  peak: "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80",
  lake: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80",
  water: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80",
  waterfall: "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1200&q=80",
  temple: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80",
  heritage: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80",
  stupa: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80",
  religious: "https://images.unsplash.com/photo-1570192977-f48187449e48?w=1200&q=80",
  wildlife: "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80",
  safari: "https://images.unsplash.com/photo-1549366021-9f761d450615?w=1200&q=80",
  park: "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1200&q=80",
  hotel: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&q=80",
  resort: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=1200&q=80",
  city: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80",
}

const isUsable = (url) => {
  if (!url || typeof url !== "string") return false
  const u = url.trim()
  if (!u) return false
  // Reject obvious placeholders
  if (u.includes("placeholder")) return false
  // Reject the old bundled /images/destinations/<place>/img1..img5.jpg
  // solid-colour blocks (~8KB) — but ALLOW the new curated named photos
  // (e.g. sunrise-view.jpg, fewatal.jpg, base-camp.jpg, safari.jpg, ...).
  if (/\/images\/destinations\/[^/]+\/img\d+\.jpg(\?|$)/.test(u)) return false
  return true
}

const pickFromPool = (seed) => {
  const s = String(seed || "nepal")
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return FALLBACK_POOL[h % FALLBACK_POOL.length]
}

/**
 * Return a usable image URL for a destination/hotel/card.
 * @param {object} destination - object that may carry cover_image_url,
 *   cover_image, image, image_url, or gallery images.
 */
export const getDestinationImageUrl = (destination) => {
  if (!destination) return FALLBACK_POOL[0]

  // 1. Explicit cover image from API / DB (backend now resolves external
  //    URLs correctly, so these are real, loadable photo URLs)
  const cover =
    destination.cover_image_url ||
    destination.cover_image ||
    destination.image_url ||
    destination.image
  if (isUsable(cover)) return cover

  // 2. Attached gallery photos
  if (Array.isArray(destination.gallery) && destination.gallery.length > 0) {
    for (const g of destination.gallery) {
      const gUrl = g?.display_url || g?.external_url || g?.image || g?.url
      if (isUsable(gUrl)) return gUrl
    }
  }

  // 2b. Local curated Nepal photo for specific named destinations
  const haystack = `${destination.name || ""} ${destination.city || ""} ${destination.district || ""}`
  const local = lookupLocalNepal(haystack)
  if (local) return local

  // 3. Category-aware fallback
  const cat = String(
    destination.category_name ||
      destination.category?.name ||
      destination.category ||
      ""
  ).toLowerCase()
  for (const [key, url] of Object.entries(CATEGORY_FALLBACK)) {
    if (cat.includes(key)) return url
  }

  // 4. Name/city keyword fallback
  for (const [key, url] of Object.entries(CATEGORY_FALLBACK)) {
    if (haystack.toLowerCase().includes(key)) return url
  }

  // 5. Stable varied pool pick (different per name, same per place)
  return pickFromPool(destination.name || destination.id || "nepal")
}

/**
 * Return a usable image URL for a hotel. Mirrors getDestinationImageUrl but
 * prefers hotel-specific fields.
 */
export const getHotelImageUrl = (hotel) => {
  if (!hotel) return CATEGORY_FALLBACK.hotel
  const cover = hotel.image_url || hotel.cover_image_url || hotel.cover_image || hotel.external_image_url
  if (isUsable(cover)) return cover
  if (Array.isArray(hotel.gallery) && hotel.gallery.length > 0) {
    const gUrl = hotel.gallery[0]?.external_url || hotel.gallery[0]?.image
    if (isUsable(gUrl)) return gUrl
  }
  return pickFromPool(hotel.name || hotel.id || "hotel")
}

export const createLocalImagePreview = (file) => {
  if (!file) return null
  return URL.createObjectURL(file)
}

/** A single sensible default image (e.g. for og:image / empties). */
export const DEFAULT_DESTINATION_IMAGE = FALLBACK_POOL[0]

/** Re-export the curated local photo map for PlaceholderImage. */
export const LOCAL_NEPAL_PHOTOS_PLACEHOLDER = LOCAL_NEPAL_PHOTOS
