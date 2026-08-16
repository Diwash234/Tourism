/**
 * frontend/Tourism/src/utils/imageUtils.js
 *
 * Central image resolver for the Nepal Tourism app.
 *
 * Priority:
 *  1. Backend-provided cover_image_url / external_url (curated AI photos
 *     for named landmarks + unique SVG postcards for everything else).
 *  2. First APPROVED gallery image.
 *  3. Local curated /images/destinations/... JPEGs for known landmarks.
 *  4. Deterministic SVG postcard via /api/v1/postcard/ endpoint (NEVER a
 *     generic Unsplash photo that repeats across destinations).
 *
 * No more generic stock-photo fallbacks — every destination gets a unique,
 * Nepal-themed visual.
 */

// Curated Nepal-specific AI photos bundled with the frontend.
// Slug keys are matched against destination name/city/district.
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
  pashupatinath:   "/images/destinations/pashupatinath/main-temple.jpg",
  boudhanath:      "/images/destinations/boudhanath/stupa.jpg",
  boudha:          "/images/destinations/boudhanath/stupa.jpg",
  swayambhunath:   "/images/destinations/swayambhunath/stupa.jpg",
  swayambhu:       "/images/destinations/swayambhunath/stupa.jpg",
  dharahara:       "/images/destinations/dharahara/tower.jpg",
  "bhimsen tower": "/images/destinations/dharahara/tower.jpg",
  // Bhaktapur / Patan / Lalitpur
  bhaktapur:       "/images/destinations/bhaktapur/durbar.jpg",
  "bhaktapur durbar": "/images/destinations/bhaktapur/durbar.jpg",
  patan:           "/images/destinations/patan/durbar-square.jpg",
  lalitpur:        "/images/destinations/patan/durbar-square.jpg",
  "patan durbar":  "/images/destinations/patan/durbar-square.jpg",
  // Chitwan
  chitwan:         "/images/destinations/chitwan/safari.jpg",
  "chitwan national park": "/images/destinations/chitwan/safari.jpg",
  sauraha:         "/images/destinations/chitwan/safari.jpg",
  // Lumbini
  lumbini:         "/images/destinations/lumbini/garden.jpg",
  // Annapurna / Ghandruk / Sarangkot
  annapurna:       "/images/destinations/annapurna/trek.jpg",
  "annapurna circuit": "/images/destinations/annapurna/trek.jpg",
  "annapurna base camp": "/images/destinations/annapurna/trek.jpg",
  abc:             "/images/destinations/annapurna/trek.jpg",
  ghandruk:        "/images/destinations/ghandruk/village.jpg",
  sarangkot:       "/images/destinations/sarangkot/view.jpg",
  "poon hill":     "/images/destinations/annapurna/trek.jpg",
  // Mustang / Muktinath
  mustang:         "/images/destinations/mustang/lo-manthang.jpg",
  "upper mustang": "/images/destinations/mustang/lo-manthang.jpg",
  "lo manthang":   "/images/destinations/mustang/lo-manthang.jpg",
  muktinath:       "/images/destinations/muktinath/temple.jpg",
  jomsom:          "/images/destinations/mustang/lo-manthang.jpg",
  kagbeni:         "/images/destinations/mustang/lo-manthang.jpg",
  marpha:          "/images/destinations/mustang/lo-manthang.jpg",
  // Ilam / tea / Kanyam
  ilam:            "/images/destinations/ilam/tea-gardens.jpg",
  "ilam tea":      "/images/destinations/ilam/tea-gardens.jpg",
  kanyam:          "/images/destinations/kanyam/tea-garden.jpg",
  "shree antu":    "/images/destinations/ilam/tea-gardens.jpg",
  // Janakpur
  janakpur:        "/images/destinations/janakpur/janaki-mandir.jpg",
  "janaki mandir": "/images/destinations/janakpur/janaki-mandir.jpg",
  "janakpur dham": "/images/destinations/janakpur/janaki-mandir.jpg",
  // Bandipur / Gorkha / Dhulikhel / Tansen / Rani Mahal
  bandipur:        "/images/destinations/bandipur/hilltop-village.jpg",
  gorkha:          "/images/destinations/gorkha/durbar.jpg",
  "gorkha durbar": "/images/destinations/gorkha/durbar.jpg",
  dhulikhel:       "/images/destinations/dhulikhel/town.jpg",
  tansen:          "/images/destinations/rani-mahal/palace.jpg",
  "rani mahal":    "/images/destinations/rani-mahal/palace.jpg",
  // Bardiya / Chitwan wildlife
  bardiya:         "/images/destinations/bardiya/tiger-reserve.jpg",
  "bardiya national park": "/images/destinations/bardiya/tiger-reserve.jpg",
  bardia:          "/images/destinations/bardiya/tiger-reserve.jpg",
  // Dolpo / Phoksundo
  dolpo:           "/images/destinations/dolpo/highland-village.jpg",
  "upper dolpo":   "/images/destinations/dolpo/highland-village.jpg",
  phoksundo:       "/images/destinations/phoksundo/lake.jpg",
  "phoksundo lake": "/images/destinations/phoksundo/lake.jpg",
  "shey phoksundo": "/images/destinations/phoksundo/lake.jpg",
  // Gosaikunda / Langtang
  gosaikunda:      "/images/destinations/gosaikunda/glacial-lake.jpg",
  gosainkunda:     "/images/destinations/gosaikunda/glacial-lake.jpg",
  langtang:        "/images/destinations/langtang/valley.jpg",
  "langtang valley": "/images/destinations/langtang/valley.jpg",
  // Koshi Tappu
  "koshi tappu":   "/images/destinations/koshi-tappu/wetlands.jpg",
  "kosi tappu":    "/images/destinations/koshi-tappu/wetlands.jpg",
  // Manaslu
  manaslu:         "/images/destinations/manaslu/mountain-peak.jpg",
  "manaslu circuit": "/images/destinations/manaslu/mountain-peak.jpg",
  // Rara
  rara:            "/images/destinations/rara/alpine-lake.jpg",
  "rara lake":     "/images/destinations/rara/alpine-lake.jpg",
  // Tilicho
  tilicho:         "/images/destinations/tilicho/himalayan-lake.jpg",
  "tilicho lake":  "/images/destinations/tilicho/himalayan-lake.jpg",
  // Peaks
  dhaulagiri:      "/images/destinations/dhaulagiri/peak.jpg",
  kanchenjunga:    "/images/destinations/kanchenjunga/peak.jpg",
  kanchanjunga:    "/images/destinations/kanchenjunga/peak.jpg",
  // Rivers / adventure
  "bhote koshi":   "/images/destinations/bhote-koshi/rafting.jpg",
  // Chandragiri
  chandragiri:     "/images/destinations/chandragiri/view.jpg",
  // Manakamana
  manakamana:      "/images/destinations/manakamana/temple.jpg",
  // Caves / falls
  "mahendra cave": "/images/destinations/mahendra-cave/interior.jpg",
  "davis falls":   "/images/destinations/davis-falls/waterfall.jpg",
  "patale chhango": "/images/destinations/davis-falls/waterfall.jpg",
  // Khaptad / Pathibhara
  khaptad:         "/images/destinations/khaptad/landscape.jpg",
  pathibhara:      "/images/destinations/pathibhara/temple.jpg",
  "pathibhara devi": "/images/destinations/pathibhara/temple.jpg",
}

const lookupLocalNepal = (name) => {
  if (!name) return null
  const n = String(name).toLowerCase().trim()
  if (LOCAL_NEPAL_PHOTOS[n]) return LOCAL_NEPAL_PHOTOS[n]
  // Longest-key substring match (more specific names first)
  let best = null
  let bestLen = 0
  for (const key of Object.keys(LOCAL_NEPAL_PHOTOS)) {
    if (n.includes(key) && key.length > bestLen) {
      best = LOCAL_NEPAL_PHOTOS[key]
      bestLen = key.length
    }
  }
  return best
}

// Map category slugs/keywords to postcard categories
const CATEGORY_FOR_POSTCARD = [
  [/(waterfall|jharna|chhango|fall)/i, "waterfalls"],
  [/(cave|gufa|mahadev cave)/i, "caves"],
  [/(hot.?spring|tatopani)/i, "hot-springs"],
  [/(lake|tal|pokhari|kunda|sarovar|daha)/i, "lakes"],
  [/(river|khola|kosi|koshi|karnali|gandaki|trishuli|narayani)/i, "rivers"],
  [/(trek|hik|base camp|circuit|pass|la)/i, "trekking"],
  [/(peak|mountain|mount |everest|sagarmatha|annapurna|manaslu|dhaulagiri|makalu|kanchenjunga|himal)/i, "mountains"],
  [/(stupa|gompa|monastery|buddhist|buddha|vihar|lumbini|boudha|swayambhu)/i, "buddhist-sites"],
  [/(temple|mandir|mahadev|shiva|bhairav|kumari|devi|bhagwati|narayan|ganesh|pashupati|muktinath|manakamana)/i, "temples"],
  [/(durbar|palace|heritage|museum|narayanhiti)/i, "heritage"],
  [/(national park|wildlife|safari|rhino|tiger|elephant|bardiya|chitwan)/i, "wildlife"],
  [/(bird|wetland|koshi tappu)/i, "bird-watching"],
  [/(forest|jungle|rhododendron|sal )/i, "forests"],
  [/(viewpoint|view point|view tower|danda|hill station|nagarkot|chandragiri|sarangkot|poon.?hill)/i, "viewpoints"],
  [/(tea garden|tea estate|ilam|kanyam)/i, "tea-coffee"],
  [/(garden|park|botanical)/i, "parks-gardens"],
  [/(cable.?car|ropeway)/i, "cablecar"],
  [/(festival|jatra|mela|dashain|tihar|holi)/i, "festivals"],
  [/(paragliding|ultralight|skydive|zip.?flyer)/i, "air-sports"],
  [/(rafting|kayak|boating|canoeing)/i, "water-sports"],
  [/(bungee|rock climb|bouldering|canyoning|climbing)/i, "adventure"],
  [/(camp|tent)/i, "camping"],
  [/(cycling|mountain bike|biking)/i, "cycling"],
  [/(snow|winter|ski|kalinchowk)/i, "winter"],
  [/(scenic|highway|road trip)/i, "scenic-routes"],
  [/(eco.?tourism|community|organic)/i, "eco-tourism"],
  [/(farm|agriculture|terrace|rice)/i, "agriculture"],
  [/(restaurant|cafe|momo|food|culinary|dal bhat)/i, "food-culinary"],
  [/(shop|market|bazaar|bazar|store)/i, "shopping"],
  [/(village|gaun)/i, "villages"],
  [/(hotel|resort|lodge|guesthouse|hostel|motel|homestay|inn)/i, "hotel"],
  [/(city|thamel|kathmandu|pokhara|biratnagar|birgunj|nepalgunj|dharan|butwal)/i, "cities"],
  [/(hill)/i, "hills"],
  [/(valley)/i, "valleys"],
]

const deriveCategory = (dest) => {
  if (!dest) return "general"
  const slug = dest.category?.slug || dest.category_slug
  if (slug && typeof slug === "string") return slug
  const catName = dest.category_name || dest.category?.name
  const hay = `${dest.name || ""} ${dest.city || ""} ${dest.district || ""} ${catName || ""} ${slug || ""}`
  for (const [re, cat] of CATEGORY_FOR_POSTCARD) {
    if (re.test(hay)) return cat
  }
  return "general"
}

const postcardUrl = (dest) => {
  const cat = deriveCategory(dest)
  const name = encodeURIComponent(dest.name || "Nepal")
  const dist = encodeURIComponent(dest.district || dest.city || "")
  return `/api/v1/postcard/${cat}/${name}/${dist}`
}

const isUsable = (url) => {
  if (!url || typeof url !== "string") return false
  const u = url.trim()
  if (!u) return false
  if (u.includes("placeholder")) return false
  return true
}

/**
 * Return a usable image URL for a destination/hotel/card.
 */
export const getDestinationImageUrl = (destination) => {
  if (!destination) return postcardUrl({ name: "Nepal" })

  // 1. Explicit cover image from API / DB
  const cover =
    destination.cover_image_url ||
    destination.cover_image ||
    destination.image_url ||
    destination.image
  if (isUsable(cover)) return cover

  // 2. Gallery (approved only if we know status)
  if (Array.isArray(destination.gallery) && destination.gallery.length > 0) {
    for (const g of destination.gallery) {
      if (g.verification_status && g.verification_status !== "approved") continue
      const gUrl = g?.display_url || g?.external_url || g?.image || g?.url
      if (isUsable(gUrl)) return gUrl
    }
  }

  // 3. Local curated Nepal photos for known landmarks
  const haystack = `${destination.name || ""} ${destination.city || ""} ${destination.district || ""}`
  const local = lookupLocalNepal(haystack)
  if (local) return local

  // 4. Deterministic SVG postcard (unique per destination — no repeats!)
  return postcardUrl(destination)
}

/**
 * Return a usable image URL for a hotel.
 */
export const getHotelImageUrl = (hotel) => {
  if (!hotel) return postcardUrl({ name: "Hotel", category: { slug: "hotel" } })
  const cover = hotel.image_url || hotel.cover_image_url || hotel.cover_image || hotel.external_image_url
  if (isUsable(cover)) return cover
  if (Array.isArray(hotel.gallery) && hotel.gallery.length > 0) {
    for (const g of hotel.gallery) {
      if (g.verification_status && g.verification_status !== "approved") continue
      const gUrl = g?.display_url || g?.external_url || g?.image
      if (isUsable(gUrl)) return gUrl
    }
  }
  return postcardUrl({ name: hotel.name || "Hotel", category: { slug: "hotel" } })
}

export const createLocalImagePreview = (file) => {
  if (!file) return null
  return URL.createObjectURL(file)
}

/** Default image for og:image / empties. */
export const DEFAULT_DESTINATION_IMAGE = "/images/destinations/everest/base-camp.jpg"

export const LOCAL_NEPAL_PHOTOS_PLACEHOLDER = LOCAL_NEPAL_PHOTOS
