/**
 * frontend/Tourism/src/utils/imageUtils.js
 *
 * Central image resolver for the Nepal Tourism app.
 *
 * Multi-source fallback chain (each tier only used when the previous one
 * has no usable image):
 *  1. Backend-provided cover_image_url / external_url (real verified
 *     Wikimedia Commons / Flickr / WordPress.org photos + curated AI
 *     landmark photos) and the API `images[]` array.
 *  2. First APPROVED gallery image.
 *  3. Local curated /images/destinations/... JPEGs for known landmarks.
 *  4. Deterministic multi-source fallback pool (Unsplash landscape photos
 *     + the local landmark photos) — picked by name hash so each
 *     destination is stable and neighbours rarely repeat.
 *  5. Unique deterministic SVG postcard via /api/v1/postcard/ endpoint
 *     (absolute last resort — never a shared generic photo).
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

// ---------------------------------------------------------------------------
// EXTRA LOCAL LANDMARK MAP — many more place names -> the best-matching local
// landmark photo, so destination pages show a real Nepal photo instead of an
// SVG postcard whenever the place is known.
// ---------------------------------------------------------------------------
const EXTRA_LOCAL_PHOTOS = {
  // Kathmandu Valley
  thamel: "/images/destinations/kathmandu/durbar-square.jpg",
  asan: "/images/destinations/kathmandu/durbar-square.jpg",
  "kathmandu durbar square": "/images/destinations/kathmandu/durbar-square.jpg",
  "hanuman dhoka": "/images/destinations/kathmandu/durbar-square.jpg",
  kirtipur: "/images/destinations/kathmandu/durbar-square.jpg",
  balaju: "/images/destinations/kathmandu/durbar-square.jpg",
  budhanilkantha: "/images/destinations/kathmandu/durbar-square.jpg",
  "swayambhu stupa": "/images/destinations/swayambhunath/stupa.jpg",
  "boudhanath stupa": "/images/destinations/boudhanath/stupa.jpg",
  "boudha stupa": "/images/destinations/boudhanath/stupa.jpg",
  pashupati: "/images/destinations/pashupatinath/main-temple.jpg",
  "pashupatinath temple": "/images/destinations/pashupatinath/main-temple.jpg",
  guhyeshwari: "/images/destinations/pashupatinath/main-temple.jpg",
  "chandragiri hill": "/images/destinations/chandragiri/view.jpg",
  "chandragiri cable": "/images/destinations/chandragiri/view.jpg",
  phulchowki: "/images/destinations/chandragiri/view.jpg",
  nagarkot: "/images/destinations/nagarkot/sunrise-view.jpg",
  dhulikhel: "/images/destinations/dhulikhel/town.jpg",
  panauti: "/images/destinations/bhaktapur/durbar.jpg",
  banepa: "/images/destinations/bhaktapur/durbar.jpg",
  changunarayan: "/images/destinations/bhaktapur/durbar.jpg",
  kakani: "/images/destinations/nagarkot/sunrise-view.jpg",
  // Bhaktapur / Patan
  "bhaktapur durbar square": "/images/destinations/bhaktapur/durbar.jpg",
  nyatapola: "/images/destinations/bhaktapur/durbar.jpg",
  "patan durbar square": "/images/destinations/patan/durbar-square.jpg",
  "krishna mandir": "/images/destinations/patan/durbar-square.jpg",
  "golden temple": "/images/destinations/patan/durbar-square.jpg",
  // Pokhara
  phewa: "/images/destinations/pokhara/fewatal.jpg",
  fewa: "/images/destinations/pokhara/fewatal.jpg",
  lakeside: "/images/destinations/pokhara/fewatal.jpg",
  "tal barahi": "/images/destinations/pokhara/fewatal.jpg",
  "world peace pagoda": "/images/destinations/pokhara/fewatal.jpg",
  "shanti stupa": "/images/destinations/pokhara/fewatal.jpg",
  "davis falls": "/images/destinations/davis-falls/waterfall.jpg",
  "devi's falls": "/images/destinations/davis-falls/waterfall.jpg",
  "patale chhango": "/images/destinations/davis-falls/waterfall.jpg",
  "mahendra cave": "/images/destinations/mahendra-cave/interior.jpg",
  "bat cave": "/images/destinations/mahendra-cave/interior.jpg",
  bindabasini: "/images/destinations/pokhara/fewatal.jpg",
  sarangkot: "/images/destinations/sarangkot/view.jpg",
  "poon hill": "/images/destinations/annapurna/trek.jpg",
  ghorepani: "/images/destinations/annapurna/trek.jpg",
  ghandruk: "/images/destinations/ghandruk/village.jpg",
  dhampus: "/images/destinations/ghandruk/village.jpg",
  "australian camp": "/images/destinations/ghandruk/village.jpg",
  bandipur: "/images/destinations/bandipur/hilltop-village.jpg",
  // Mountains
  everest: "/images/destinations/everest/base-camp.jpg",
  sagarmatha: "/images/destinations/everest/base-camp.jpg",
  "everest base camp": "/images/destinations/everest/base-camp.jpg",
  khumbu: "/images/destinations/everest/base-camp.jpg",
  namche: "/images/destinations/everest/base-camp.jpg",
  tengboche: "/images/destinations/everest/base-camp.jpg",
  lukla: "/images/destinations/everest/base-camp.jpg",
  amadablam: "/images/destinations/everest/base-camp.jpg",
  annapurna: "/images/destinations/annapurna/trek.jpg",
  "annapurna base camp": "/images/destinations/annapurna/trek.jpg",
  "annapurna circuit": "/images/destinations/annapurna/trek.jpg",
  "abc trek": "/images/destinations/annapurna/trek.jpg",
  manaslu: "/images/destinations/manaslu/mountain-peak.jpg",
  "manaslu circuit": "/images/destinations/manaslu/mountain-peak.jpg",
  dhaulagiri: "/images/destinations/dhaulagiri/peak.jpg",
  kanchenjunga: "/images/destinations/kanchenjunga/peak.jpg",
  makalu: "/images/destinations/kanchenjunga/peak.jpg",
  gosaikunda: "/images/destinations/gosaikunda/glacial-lake.jpg",
  langtang: "/images/destinations/langtang/valley.jpg",
  "kyanjin gompa": "/images/destinations/langtang/valley.jpg",
  // Mustang / Dolpo
  mustang: "/images/destinations/mustang/lo-manthang.jpg",
  "lo manthang": "/images/destinations/mustang/lo-manthang.jpg",
  jomsom: "/images/destinations/mustang/lo-manthang.jpg",
  kagbeni: "/images/destinations/mustang/lo-manthang.jpg",
  marpha: "/images/destinations/mustang/lo-manthang.jpg",
  muktinath: "/images/destinations/muktinath/temple.jpg",
  tilicho: "/images/destinations/tilicho/himalayan-lake.jpg",
  dolpo: "/images/destinations/dolpo/highland-village.jpg",
  phoksundo: "/images/destinations/phoksundo/lake.jpg",
  "shey phoksundo": "/images/destinations/phoksundo/lake.jpg",
  // Lakes
  rara: "/images/destinations/rara/alpine-lake.jpg",
  "rara lake": "/images/destinations/rara/alpine-lake.jpg",
  "phewa lake": "/images/destinations/pokhara/fewatal.jpg",
  begnas: "/images/destinations/pokhara/fewatal.jpg",
  "rupa lake": "/images/destinations/pokhara/fewatal.jpg",
  gokyo: "/images/destinations/rara/alpine-lake.jpg",
  imja: "/images/destinations/rara/alpine-lake.jpg",
  // West Nepal
  "khaptad lake": "/images/destinations/khaptad/landscape.jpg",
  "api himal": "/images/destinations/khaptad/landscape.jpg",
  saipal: "/images/destinations/khaptad/landscape.jpg",
  "rani mahal": "/images/destinations/rani-mahal/palace.jpg",
  // Terai / wildlife
  sauraha: "/images/destinations/chitwan/safari.jpg",
  "chitwan national park": "/images/destinations/chitwan/safari.jpg",
  bardia: "/images/destinations/bardiya/tiger-reserve.jpg",
  "bardiya national park": "/images/destinations/bardiya/tiger-reserve.jpg",
  "koshi tappu": "/images/destinations/koshi-tappu/wetlands.jpg",
  "kosi tappu": "/images/destinations/koshi-tappu/wetlands.jpg",
  shuklaphanta: "/images/destinations/bardiya/tiger-reserve.jpg",
  "parsa national park": "/images/destinations/chitwan/safari.jpg",
  "banke national park": "/images/destinations/bardiya/tiger-reserve.jpg",
  "maya devi": "/images/destinations/lumbini/garden.jpg",
  "lumbini garden": "/images/destinations/lumbini/garden.jpg",
  // East / tea
  "ilam tea": "/images/destinations/ilam/tea-gardens.jpg",
  "shree antu": "/images/destinations/ilam/tea-gardens.jpg",
  birtamod: "/images/destinations/ilam/tea-gardens.jpg",
  "janaki mandir": "/images/destinations/janakpur/janaki-mandir.jpg",
  "janakpur dham": "/images/destinations/janakpur/janaki-mandir.jpg",
  // Gorkha / Manakamana
  "gorkha durbar": "/images/destinations/gorkha/durbar.jpg",
  // Misc landmarks
  dharahara: "/images/destinations/dharahara/tower.jpg",
  "bhimsen tower": "/images/destinations/dharahara/tower.jpg",
  "bhote koshi": "/images/destinations/bhote-koshi/rafting.jpg",
  trishuli: "/images/destinations/bhote-koshi/rafting.jpg",
  bungee: "/images/destinations/bhote-koshi/rafting.jpg",
  rafting: "/images/destinations/bhote-koshi/rafting.jpg",
  "garden of dreams": "/images/destinations/kathmandu/durbar-square.jpg",
  ranipokhari: "/images/destinations/kathmandu/durbar-square.jpg",
  kumari: "/images/destinations/kathmandu/durbar-square.jpg",
}

Object.assign(LOCAL_NEPAL_PHOTOS, EXTRA_LOCAL_PHOTOS)

// ---------------------------------------------------------------------------
// SEMANTIC PHOTO TYPES — every local landmark photo is tagged so we never
// show a lake photo on a temple, a tiger photo on a temple, a rafting photo
// on a highway, etc. Matching is NAME-ONLY (never city/district), so Pokhara
// destinations no longer all show the same lakeside image and Lalitpur
// places no longer all show the Patan photo.
// ---------------------------------------------------------------------------
const LOCAL_PHOTO_TYPES = {
  "/images/destinations/nagarkot/sunrise-view.jpg": "viewpoint",
  "/images/destinations/pokhara/fewatal.jpg": "lake",
  "/images/destinations/everest/base-camp.jpg": "mountain",
  "/images/destinations/kathmandu/durbar-square.jpg": "heritage",
  "/images/destinations/pashupatinath/main-temple.jpg": "temple",
  "/images/destinations/boudhanath/stupa.jpg": "buddhist",
  "/images/destinations/swayambhunath/stupa.jpg": "buddhist",
  "/images/destinations/dharahara/tower.jpg": "city",
  "/images/destinations/bhaktapur/durbar.jpg": "heritage",
  "/images/destinations/patan/durbar-square.jpg": "heritage",
  "/images/destinations/chitwan/safari.jpg": "wildlife",
  "/images/destinations/lumbini/garden.jpg": "buddhist",
  "/images/destinations/annapurna/trek.jpg": "mountain",
  "/images/destinations/ghandruk/village.jpg": "village",
  "/images/destinations/sarangkot/view.jpg": "viewpoint",
  "/images/destinations/mustang/lo-manthang.jpg": "heritage",
  "/images/destinations/muktinath/temple.jpg": "temple",
  "/images/destinations/ilam/tea-gardens.jpg": "farm",
  "/images/destinations/kanyam/tea-garden.jpg": "farm",
  "/images/destinations/janakpur/janaki-mandir.jpg": "temple",
  "/images/destinations/bandipur/hilltop-village.jpg": "village",
  "/images/destinations/gorkha/durbar.jpg": "heritage",
  "/images/destinations/dhulikhel/town.jpg": "city",
  "/images/destinations/rani-mahal/palace.jpg": "heritage",
  "/images/destinations/bardiya/tiger-reserve.jpg": "wildlife",
  "/images/destinations/dolpo/highland-village.jpg": "village",
  "/images/destinations/phoksundo/lake.jpg": "lake",
  "/images/destinations/gosaikunda/glacial-lake.jpg": "lake",
  "/images/destinations/langtang/valley.jpg": "mountain",
  "/images/destinations/koshi-tappu/wetlands.jpg": "wildlife",
  "/images/destinations/manaslu/mountain-peak.jpg": "mountain",
  "/images/destinations/rara/alpine-lake.jpg": "lake",
  "/images/destinations/tilicho/himalayan-lake.jpg": "lake",
  "/images/destinations/dhaulagiri/peak.jpg": "mountain",
  "/images/destinations/kanchenjunga/peak.jpg": "mountain",
  "/images/destinations/bhote-koshi/rafting.jpg": "adventure",
  "/images/destinations/chandragiri/view.jpg": "viewpoint",
  "/images/destinations/manakamana/temple.jpg": "temple",
  "/images/destinations/mahendra-cave/interior.jpg": "cave",
  "/images/destinations/davis-falls/waterfall.jpg": "waterfall",
  "/images/destinations/khaptad/landscape.jpg": "mountain",
  "/images/destinations/pathibhara/temple.jpg": "temple",
}

// Destination category -> acceptable photo types (preferred first).
const CATEGORY_TYPES = {
  temple: ["temple", "buddhist", "heritage"],
  pilgrimage: ["temple", "buddhist", "heritage"],
  religious: ["temple", "buddhist", "heritage"],
  "buddhist-sites": ["buddhist", "temple", "heritage"],
  lakes: ["lake"],
  rivers: ["waterfall", "lake", "adventure"],
  waterfalls: ["waterfall"],
  caves: ["cave"],
  mountains: ["mountain"],
  peaks: ["mountain"],
  viewpoint: ["viewpoint", "mountain"],
  viewpoints: ["viewpoint", "mountain"],
  hills: ["viewpoint", "mountain"],
  valleys: ["mountain", "viewpoint"],
  wildlife: ["wildlife"],
  "national parks": ["wildlife"],
  "bird-watching": ["wildlife"],
  forests: ["mountain", "wildlife"],
  villages: ["village"],
  cities: ["city", "heritage"],
  heritage: ["heritage", "city"],
  museums: ["heritage"],
  trekking: ["mountain", "adventure", "viewpoint"],
  adventure: ["adventure", "mountain"],
  "air-sports": ["adventure", "viewpoint"],
  "water-sports": ["adventure", "waterfall", "lake"],
  "hot-springs": ["waterfall", "lake"],
  "tea-coffee": ["farm"],
  winter: ["mountain"],
  "scenic-routes": ["viewpoint", "mountain"],
  "eco-tourism": ["village", "mountain"],
  hotel: ["hotel"],
  "guest_house": ["hotel"],
  hostel: ["hotel"],
  resort: ["hotel"],
  homestay: ["hotel"],
  "home_stay": ["hotel"],
  motel: ["hotel"],
  apartment: ["hotel"],
  "camp_site": ["mountain", "wildlife"],
  chalet: ["hotel"],
  "alpine_hut": ["hotel", "mountain"],
  "wilderness_hut": ["hotel", "mountain"],
  food: ["heritage", "city"],
  "food-culinary": ["heritage", "city"],
  shopping: ["heritage", "city"],
  festivals: ["heritage", "city"],
  "parks-gardens": ["viewpoint", "heritage"],
  "natural-wonders": ["mountain", "lake", "viewpoint"],
}

const normalizeName = (s) => String(s || "").toLowerCase().trim().replace(/\s+/g, " ")

const lookupLocalNepal = (name, categoryType) => {
  if (!name) return null
  const n = normalizeName(name)
  // 1. Exact full-name match always wins (e.g. "Pokhara", "Phewa Lake")
  if (LOCAL_NEPAL_PHOTOS[n]) return LOCAL_NEPAL_PHOTOS[n]
  // 2. Longest-key substring match — NAME ONLY — respecting photo type.
  const allowed = CATEGORY_TYPES[categoryType] || null
  let best = null
  let bestLen = 0
  for (const key of Object.keys(LOCAL_NEPAL_PHOTOS)) {
    if (n.includes(key) && key.length > bestLen) {
      const path = LOCAL_NEPAL_PHOTOS[key]
      const ptype = LOCAL_PHOTO_TYPES[path] || "any"
      if (!allowed || allowed.includes(ptype) || ptype === "any") {
        best = path
        bestLen = key.length
      }
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

export const postcardUrl = (dest) => {
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
  // SVG postcards are the LAST resort — treat them as "no real photo" so the
  // local landmark photo / multi-source pool can take over first.
  if (u.includes("/api/v1/postcard/")) return false
  return true
}

// ---------------------------------------------------------------------------
// Multi-source fallback pool (Unsplash + local landmarks)
// ---------------------------------------------------------------------------
const UNSPLASH_POOL = [
  "photo-1506905925346-21bda4d32df4", "photo-1464822759023-fed622ff2c3b",
  "photo-1506744038136-46273834b3fb", "photo-1544735716-392fe2489ffa",
  "photo-1470071459604-3b5ec3a7fe05", "photo-1501785888041-af3ef285b470",
  "photo-1441974231531-c6227db76b6e", "photo-1476514525535-07fb3b4ae5f1",
  "photo-1507525428034-b723cf961d3e", "photo-1519681393784-d120267933ba",
  "photo-1502786129293-79981df4e689", "photo-1486870591958-9b9d0d1dda99",
  "photo-1526778548025-fa2f459cd5c1", "photo-1565008447742-97f6f38c985c",
  "photo-1575550959106-5a7defe28b56", "photo-1605649487212-47bdab064df7",
  "photo-1609766428351-8e1a5c4e8e8a", "photo-1605640840605-14ac1855827b",
  "photo-1546484475-7f7bd55792da", "photo-1558981359-219d6364c9c8",
  "photo-1589308078056-3eb0e4a3a5c5", "photo-1589308078058-c6dba4792c60",
  "photo-1439066615861-d1af74d74000", "photo-1454496522488-7a8e488e8606",
  "photo-1470770841072-f978cf4d019e", "photo-1483728642387-6c3bdd6c93e5",
  "photo-1500534623283-312aade485b7", "photo-1518002171953-a080ee817e1f",
  "photo-1518709594023-6eab9bab7b23", "photo-1524492412937-b28074a5d7da",
  "photo-1544198365-f5d60b6d8190", "photo-1544967082-d9d25d867d66",
  "photo-1546182990-dffeafbe841d", "photo-1548013146-72479768bada",
  "photo-1549366021-9f761d450615", "photo-1568322445389-f64ac2515020",
  "photo-1570192977-f48187449e48", "photo-1571401835393-8c5f35328320",
  "photo-1571847140471-1d7766e825ea", "photo-1572953107300-18597face4ba",
  "photo-1582650625119-3a31f8418b7d", "photo-1583212292454-1fe6229603b7",
  "photo-1585511582812-88478e0a2705", "photo-1590766940554-153d9e0b2eff",
  "photo-1602088113235-229c19758e9c", "photo-1626621331169-5f34be280ed9",
].map((id) => `https://images.unsplash.com/${id}?w=1200&auto=format&fit=crop&q=80`)

export const FALLBACK_POOL = [...Object.values(LOCAL_NEPAL_PHOTOS), ...UNSPLASH_POOL]

// Unsplash photos tagged by semantic type for category-aware fallbacks.
const U = (id) => `https://images.unsplash.com/${id}?w=1200&auto=format&fit=crop&q=80`
const UNSPLASH_TYPED = {
  mountain: [U("photo-1464822759023-fed622ff2c3b"), U("photo-1506905925346-21bda4d32df4"), U("photo-1470071459604-3b5ec3a7fe05"), U("photo-1501785888041-af3ef285b470"), U("photo-1519681393784-d120267933ba"), U("photo-1526778548025-fa2f459cd5c1"), U("photo-1589308078056-3eb0e4a3a5c5"), U("photo-1589308078058-c6dba4792c60"), U("photo-1454496522488-7a8e488e8606"), U("photo-1544735716-392fe2489ffa"), U("photo-1558981359-219d6364c9c8")],
  lake: [U("photo-1502786129293-79981df4e689"), U("photo-1439066615861-d1af74d74000"), U("photo-1470770841072-f978cf4d019e"), U("photo-1500534623283-312aade485b7"), U("photo-1549366021-9f761d450615"), U("photo-1476514525535-07fb3b4ae5f1"), U("photo-1507525428034-b723cf961d3e"), U("photo-1486870591958-9b9d0d1dda99")],
  temple: [U("photo-1544967082-d9d25d867d66"), U("photo-1548013146-72479768bada"), U("photo-1568322445389-f64ac2515020"), U("photo-1570192977-f48187449e48"), U("photo-1571847140471-1d7766e825ea"), U("photo-1585511582812-88478e0a2705"), U("photo-1590766940554-153d9e0b2eff"), U("photo-1626621331169-5f34be280ed9"), U("photo-1605640840605-14ac1855827b"), U("photo-1524492412937-b28074a5d7da")],
  heritage: [U("photo-1605649487212-47bdab064df7"), U("photo-1609766428351-8e1a5c4e8e8a"), U("photo-1544198365-f5d60b6d8190"), U("photo-1518002171953-a080ee817e1f"), U("photo-1524492412937-b28074a5d7da"), U("photo-1546182990-dffeafbe841d")],
  city: [U("photo-1518709594023-6eab9bab7b23"), U("photo-1518002171953-a080ee817e1f"), U("photo-1544198365-f5d60b6d8190"), U("photo-1546182990-dffeafbe841d")],
  hotel: [U("photo-1566073771259-6a8506099945"), U("photo-1602088113235-229c19758e9c"), U("photo-1583212292454-1fe6229603b7"), U("photo-1546484475-7f7bd55792da"), U("photo-1571003123894-1f8a6c5b3a2e"), U("photo-1582719508461-905c673771fd")],
  village: [U("photo-1575550959106-5a7defe28b56"), U("photo-1483728642387-6c3bdd6c93e5"), U("photo-1441974231531-c6227db76b6e")],
  nature: [U("photo-1441974231531-c6227db76b6e"), U("photo-1470071459604-3b5ec3a7fe05"), U("photo-1572953107300-18597face4ba"), U("photo-1582650625119-3a31f8418b7d")],
  waterfall: [U("photo-1582650625119-3a31f8418b7d"), U("photo-1486870591958-9b9d0d1dda99")],
  wildlife: [U("photo-1546182990-dffeafbe841d"), U("photo-1441974231531-c6227db76b6e")],
}

const POOL_BY_TYPE = {}
const buildPool = (types) => {
  const out = []
  for (const t of types) {
    out.push(...(UNSPLASH_TYPED[t] || []))
    for (const [path, ptype] of Object.entries(LOCAL_PHOTO_TYPES)) {
      if (ptype === t) out.push(path)
    }
  }
  return [...new Set(out)]
}
for (const [cat, types] of Object.entries(CATEGORY_TYPES)) {
  POOL_BY_TYPE[cat] = buildPool(types)
}
POOL_BY_TYPE.hotel = [...new Set([...UNSPLASH_TYPED.hotel, ...UNSPLASH_TYPED.heritage])]

const hashStr = (s) => {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h
}

/** Deterministic category-aware fallback image for a seed (name only!). */
export const fallbackImageUrl = (seed, category) => {
  const pool = (category && POOL_BY_TYPE[category]) || FALLBACK_POOL
  return pool[hashStr(String(seed ?? "nepal")) % pool.length]
}

/** Derive the semantic category type key from a destination object. */
export const deriveImageCategory = (destination) => {
  if (!destination) return null
  const slug = destination.category?.slug || destination.category_slug || ""
  if (slug && CATEGORY_TYPES[slug]) return slug
  const catName = (destination.category_name || destination.category?.name || "").toLowerCase()
  for (const [cat, types] of Object.entries(CATEGORY_TYPES)) {
    if (catName.includes(cat)) return cat
  }
  return null
}

/**
 * Return a usable image URL for a destination/hotel/card.
 */
export const getDestinationImageUrl = (destination) => {
  if (!destination) return postcardUrl({ name: "Nepal" })

  if (Array.isArray(destination.images) && destination.images.length > 0) {
    const first = destination.images.find(isUsable)
    if (first) return first
  }

  const cover = destination.cover_image_url || destination.cover_image || destination.image_url || destination.image
  if (isUsable(cover)) return cover

  if (Array.isArray(destination.gallery) && destination.gallery.length > 0) {
    for (const g of destination.gallery) {
      if (g.verification_status && g.verification_status !== "approved") continue
      const gUrl = g?.display_url || g?.image_url || g?.external_url || g?.image || g?.url
      if (isUsable(gUrl)) return gUrl
    }
  }

  // Local curated Nepal photos — NAME-ONLY + category-aware.
  const catType = deriveImageCategory(destination)
  const local = lookupLocalNepal(destination.name, catType)
  if (local) return local

  // Category-aware multi-source fallback pool (deterministic by name)
  return fallbackImageUrl(destination.name || destination.slug || destination.id || "nepal", catType)
}

/**
 * Build a standalone-image-server URL from a relative path.
 */
export const getImageServerUrl = (path) => {
  if (!path) return ""
  const base = (import.meta.env.VITE_IMAGE_BASE_URL || "").replace(/\/+$/, "")
  if (!base) return path
  return `${base}/images/${String(path).replace(/^\/+/, "")}`
}

/**
 * Return a usable image URL for a hotel — always a hotel-appropriate real
 * photo (never a temple/lake/tiger photo from another category).
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
  const seed = hotel.name || hotel.slug || "Hotel"
  return fallbackImageUrl(seed, "hotel") || postcardUrl({ name: hotel.name || "Hotel", category: { slug: "hotel" } })
}

export const createLocalImagePreview = (file) => {
  if (!file) return null
  return URL.createObjectURL(file)
}

/** Default image for og:image / empties. */
export const DEFAULT_DESTINATION_IMAGE = "/images/destinations/everest/base-camp.jpg"

export const LOCAL_NEPAL_PHOTOS_PLACEHOLDER = LOCAL_NEPAL_PHOTOS
