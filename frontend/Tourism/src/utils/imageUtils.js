/**
 * frontend/Tourism/src/utils/imageUtils.js
 *
 * Central image resolver for the Nepal Tourism app.
 *
 * Image resolution is intentionally conservative:
 *  1. Backend-provided cover_image_url / cover (the admin-controlled field —
 *     updated by the media dashboard's set-cover/replace-cover flows), then
 *     the API `images[]` gallery array as the next tier.
 *  2. First APPROVED gallery image.
 *  3. Local curated /images/destinations/... JPEGs only when the destination
 *     name matches a known landmark mapping.
 * Unknown records return no image so the UI can show an honest unavailable
 * state instead of substituting unrelated stock media.
 */

// Curated Nepal-specific photos bundled with the frontend.
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
  // Chitwan / Bharatpur
  chitwan:         "/images/destinations/chitwan/safari.jpg",
  "chitwan national park": "/images/destinations/chitwan/safari.jpg",
  sauraha:         "/images/destinations/chitwan/safari.jpg",
  bharatpur:       "/images/destinations/chitwan/safari.jpg",
  "bharatpur metropolitan city": "/images/destinations/chitwan/safari.jpg",
  "bharatpur metropolitan": "/images/destinations/chitwan/safari.jpg",
  narayani:        "/images/destinations/chitwan/safari.jpg",
  // Lumbini
  lumbini:         "/images/destinations/lumbini/garden.jpg",
  // Annapurna / Ghandruk / Sarangkot
  annapurna:       "/images/destinations/annapurna/trek.jpg",
  "annapurna circuit": "/images/destinations/annapurna/trek.jpg",
  "annapurna base camp": "/images/destinations/annapurna/trek.jpg",
  abc:             "/images/destinations/annapurna/trek.jpg",
  ghandruk:        "/images/destinations/ghandruk/village.jpg",
  sarangkot:       "/images/destinations/annapurna/trek.jpg",
  "poon hill":     "/images/destinations/annapurna/trek.jpg",
  // Mustang / Muktinath
  mustang:         "/images/destinations/mustang/lo-manthang.jpg",
  "upper mustang": "/images/destinations/mustang/lo-manthang.jpg",
  "lo manthang":   "/images/destinations/mustang/lo-manthang.jpg",
  muktinath:       "/images/destinations/muktinath/temple.jpg",
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
  dhulikhel:       "/images/destinations/bandipur/hilltop-village.jpg",
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
  chandragiri:     "/images/destinations/nagarkot/sunrise-view.jpg",
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
  "swayambhu stupa": "/images/destinations/swayambhunath/stupa.jpg",
  "boudhanath stupa": "/images/destinations/boudhanath/stupa.jpg",
  "boudha stupa": "/images/destinations/boudhanath/stupa.jpg",
  pashupati: "/images/destinations/pashupatinath/main-temple.jpg",
  "pashupatinath temple": "/images/destinations/pashupatinath/main-temple.jpg",
  guhyeshwari: "/images/destinations/pashupatinath/main-temple.jpg",
  "chandragiri hill": "/images/destinations/nagarkot/sunrise-view.jpg",
  "chandragiri cable": "/images/destinations/nagarkot/sunrise-view.jpg",
  nagarkot: "/images/destinations/nagarkot/sunrise-view.jpg",
  dhulikhel: "/images/destinations/bandipur/hilltop-village.jpg",
  // Bhaktapur / Patan
  "bhaktapur durbar square": "/images/destinations/bhaktapur/durbar.jpg",
  nyatapola: "/images/destinations/bhaktapur/durbar.jpg",
  "patan durbar square": "/images/destinations/patan/durbar-square.jpg",
  // Pokhara
  phewa: "/images/destinations/pokhara/fewatal.jpg",
  fewa: "/images/destinations/pokhara/fewatal.jpg",
  lakeside: "/images/destinations/pokhara/fewatal.jpg",
  "davis falls": "/images/destinations/davis-falls/waterfall.jpg",
  "devi's falls": "/images/destinations/davis-falls/waterfall.jpg",
  "patale chhango": "/images/destinations/davis-falls/waterfall.jpg",
  "mahendra cave": "/images/destinations/mahendra-cave/interior.jpg",
  sarangkot: "/images/destinations/annapurna/trek.jpg",
  "poon hill": "/images/destinations/annapurna/trek.jpg",
  ghorepani: "/images/destinations/annapurna/trek.jpg",
  ghandruk: "/images/destinations/ghandruk/village.jpg",
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
  gosaikunda: "/images/destinations/gosaikunda/glacial-lake.jpg",
  langtang: "/images/destinations/langtang/valley.jpg",
  "kyanjin gompa": "/images/destinations/langtang/valley.jpg",
  // Mustang / Dolpo
  mustang: "/images/destinations/mustang/lo-manthang.jpg",
  "lo manthang": "/images/destinations/mustang/lo-manthang.jpg",
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
  // West Nepal
  "khaptad lake": "/images/destinations/khaptad/landscape.jpg",
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
  "lumbini garden": "/images/destinations/lumbini/garden.jpg",
  bharatpur: "/images/destinations/chitwan/safari.jpg",
  "bharatpur metropolitan city": "/images/destinations/chitwan/safari.jpg",
  "bharatpur metropolitan": "/images/destinations/chitwan/safari.jpg",
  // East / tea
  "ilam tea": "/images/destinations/ilam/tea-gardens.jpg",
  "shree antu": "/images/destinations/ilam/tea-gardens.jpg",
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
  kumari: "/images/destinations/kathmandu/durbar-square.jpg",
  // Round 23 — local landmark images: food (real Nepali dishes)
  momo: "/images/destinations/food/momo.jpg",
  "momo trail": "/images/destinations/food/momo.jpg",
  "bhojpur momo": "/images/destinations/food/momo.jpg",
  "sel roti": "/images/destinations/food/sel-roti.jpg",
  "juju dhau": "/images/destinations/food/juju-dhau.jpg",
  chiya: "/images/destinations/food/masala-chiya.jpg",
  "nepali chiya": "/images/destinations/food/masala-chiya.jpg",
  "masala chai": "/images/destinations/food/masala-chiya.jpg",
  "newari bhoj": "/images/destinations/food/newari-bhoj.jpg",
  "newari khaja": "/images/destinations/food/newari-bhoj.jpg",
  "samay baji": "/images/destinations/food/newari-bhoj.jpg",
  "bhojan griha": "/images/destinations/food/newari-bhoj.jpg",
  "street food": "/images/destinations/food/momo.jpg",
  "food street": "/images/destinations/food/momo.jpg",
  "thamel food": "/images/destinations/food/momo.jpg",
  // Round 23 — festivals
  holi: "/images/destinations/festivals/holi-kathmandu.jpg",
  "fagu purnima": "/images/destinations/festivals/holi-kathmandu.jpg",
  dashain: "/images/destinations/festivals/dashain-tika.jpg",
  "dashain tika": "/images/destinations/festivals/dashain-tika.jpg",
  tihar: "/images/destinations/festivals/tihar-diya.jpg",
  deepawali: "/images/destinations/festivals/tihar-diya.jpg",
  "laxmi puja": "/images/destinations/festivals/tihar-diya.jpg",
  // Round 23 — culture
  "tharu dance": "/images/destinations/culture/tharu-dance.jpg",
  tharu: "/images/destinations/culture/tharu-dance.jpg",
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
  "/images/destinations/ilam/tea-gardens.jpg": "tea",
  "/images/destinations/kanyam/tea-garden.jpg": "tea",
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
  "/images/destinations/bhote-koshi/rafting.jpg": "rafting",
  "/images/destinations/chandragiri/view.jpg": "viewpoint",
  "/images/destinations/manakamana/temple.jpg": "temple",
  "/images/destinations/mahendra-cave/interior.jpg": "cave",
  "/images/destinations/davis-falls/waterfall.jpg": "waterfall",
  // Round 23 — local food / festival / culture landmark images
  "/images/destinations/food/momo.jpg": "food",
  "/images/destinations/food/sel-roti.jpg": "food",
  "/images/destinations/food/juju-dhau.jpg": "food",
  "/images/destinations/food/masala-chiya.jpg": "food",
  "/images/destinations/food/newari-bhoj.jpg": "food",
  "/images/destinations/festivals/holi-kathmandu.jpg": "festival",
  "/images/destinations/festivals/dashain-tika.jpg": "festival",
  "/images/destinations/festivals/tihar-diya.jpg": "festival",
  "/images/destinations/culture/tharu-dance.jpg": "culture",
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
  rivers: ["waterfall", "lake", "rafting"],
  waterfalls: ["waterfall", "nature"],
  caves: ["cave", "mountain"],
  mountains: ["mountain"],
  peaks: ["mountain"],
  viewpoint: ["viewpoint", "mountain"],
  viewpoints: ["viewpoint", "mountain"],
  hills: ["viewpoint", "mountain", "nature"],
  valleys: ["mountain", "nature", "lake"],
  wildlife: ["wildlife", "nature"],
  "national-park": ["wildlife", "nature"],
  "bird-watching": ["wildlife", "nature"],
  forests: ["nature", "mountain", "wildlife"],
  villages: ["village", "nature", "mountain"],
  cities: ["city", "heritage"],
  heritage: ["heritage", "city"],
  museums: ["heritage", "culture"],
  trekking: ["mountain", "adventure", "viewpoint"],
  adventure: ["adventure", "climbing", "mountain", "air"],
  "air-sports": ["air", "adventure", "viewpoint"],
  "water-sports": ["rafting", "waterfall", "lake", "adventure"],
  "hot-springs": ["hotspring", "waterfall", "lake"],
  "hot-spring": ["hotspring", "waterfall", "lake"],
  "tea-coffee": ["tea", "farm"],
  "tea-garden": ["tea", "farm"],
  winter: ["snow", "mountain"],
  "scenic-routes": ["road", "viewpoint", "mountain"],
  "eco-tourism": ["village", "nature", "wildlife"],
  camping: ["camping", "mountain", "nature"],
  "camp_site": ["camping", "mountain", "nature"],
  cycling: ["cycling", "mountain", "adventure"],
  culture: ["culture", "heritage", "festival"],
  festivals: ["festival", "culture", "city"],
  shopping: ["shopping", "city"],
  "food-culinary": ["food", "city"],
  "parks-gardens": ["nature", "viewpoint", "heritage"],
  "natural-wonders": ["mountain", "lake", "waterfall", "nature"],
  "spiritual-wellness": ["hotspring", "temple", "nature"],
  "outdoor_activities": ["adventure", "mountain", "nature"],
  "theme_park": ["city", "festival"],
  "picnic_site": ["nature", "lake", "viewpoint"],
  "photography-spots": ["viewpoint", "mountain", "nature"],
  "heritage-temples": ["temple", "heritage"],
  "lakes-water-activities": ["lake", "rafting"],
  "nature-trekking": ["mountain", "nature", "trekking"],
  "hill-stations": ["viewpoint", "mountain", "nature"],
  "zoo": ["wildlife"],
  aquarium: ["lake", "nature"],
  artwork: ["culture", "heritage"],
  gallery: ["culture", "heritage"],
  "travel_agency": ["city", "heritage"],
  information: ["city", "heritage"],
  attraction: ["mountain", "nature", "heritage", "city", "lake", "village"],
  "camp_pitch": ["camping", "mountain", "nature"],
  hostel: ["hotel"],
  motel: ["hotel"],
  resort: ["hotel"],
  apartment: ["hotel"],
  chalet: ["hotel"],
  "alpine_hut": ["hotel", "mountain"],
  "wilderness_hut": ["hotel", "mountain"],
  "caravan_site": ["camping", "nature"],
  "trailhead": ["mountain", "nature", "trekking"],
  route: ["road", "mountain", "nature"],
  hotel: ["hotel"],
  "guest_house": ["hotel"],
  homestay: ["hotel"],
  "home_stay": ["hotel"],
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

// Automatic image fallbacks are restricted to the bundled landmark mapping above.
// Unknown records remain image-less rather than receiving unrelated stock media.

/** Deterministic category-aware fallback image for a seed (name only!). */
export const fallbackImageUrl = (seed, category) => {
  // A fallback is safe only when the place name matches a bundled landmark
  // mapping. Never hash an unknown name into an unrelated Nepal photograph.
  return lookupLocalNepal(seed, category) || ""
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

// Manually corrected media for records whose imported DB cover is known to
// depict a different attraction. These take priority until an admin replaces
// the cover through the media dashboard.
const CORRECTED_DESTINATION_MEDIA = {
  "hot air balloon pokhara": "/images/destinations/hot-air-balloon-pokhara/img1.jpg",
  "ultralight flight pokhara": "/images/destinations/ultralight-flight-pokhara/img1.jpg",
  "pokhara ultralight flights": "/images/destinations/ultralight-flight-pokhara/img1.jpg",
  "zipflyer nepal pokhara": "/images/destinations/zipflyer-pokhara/img1.jpg",
  "zipflyer pokhara": "/images/destinations/zipflyer-pokhara/img1.jpg",
  "chhoser sky caves": "/images/destinations/chhoser-sky-caves/img1.jpg",
  "gupteswor gupha": "/images/destinations/gupteswor-gupha/img1.jpg",
}

/**
 * Return a usable image URL for a destination/hotel/card.
 */
export const getDestinationImageUrl = (destination) => {
  if (!destination) return ""
  const corrected = CORRECTED_DESTINATION_MEDIA[normalizeName(destination.name)]
  if (corrected) return corrected
  // The cover field is what the admin sets (set-cover / replace-cover flows
  // update it), so it MUST win over the gallery `images[]` array — otherwise
  // admin cover changes never appear because the first (oldest) gallery
  // photo keeps taking precedence.
  const cover = destination.cover_image_url || destination.cover_image || destination.image_url || destination.image
  if (isUsable(cover)) return cover
  if (Array.isArray(destination.images)) {
    const first = destination.images.find(isUsable)
    if (first) return first
  }
  if (Array.isArray(destination.gallery)) {
    for (const media of destination.gallery) {
      if (media.verification_status === "rejected") continue
      const url = media.display_url || media.image_url || media.external_url || media.image || media.url
      if (isUsable(url)) return url
    }
  }
  // Restore the previously generated, bundled place-specific media for known
  // Nepal landmarks.
  const local = lookupLocalNepal(destination.name, deriveImageCategory(destination))
  if (local) return local
  return fallbackImageUrl(destination.name || destination.title || "Nepal Landmark", deriveImageCategory(destination)) || ""
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
  if (!hotel) return ""
  const cover = hotel.image_url || hotel.cover_image_url || hotel.cover_image || hotel.external_image_url
  if (isUsable(cover)) return cover
  if (Array.isArray(hotel.gallery)) {
    for (const media of hotel.gallery) {
      if (media.is_verified === false) continue
      if (media.verification_status && !["approved", "verified"].includes(media.verification_status)) continue
      const url = media.display_url || media.external_url || media.image
      if (isUsable(url)) return url
    }
  }
  return ""
}

export const createLocalImagePreview = (file) => {
  if (!file) return null
  return URL.createObjectURL(file)
}

/** No generic destination image is used when a record has no media. */
export const DEFAULT_DESTINATION_IMAGE = ""

export const LOCAL_NEPAL_PHOTOS_PLACEHOLDER = LOCAL_NEPAL_PHOTOS
