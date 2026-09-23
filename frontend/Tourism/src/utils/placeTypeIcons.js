import {
  FaMountain, FaGopuram, FaChurch, FaMosque, FaHiking, FaWater, FaUtensils,
  FaHotel, FaTree, FaLandmark, FaTheaterMasks, FaFish, FaCampground,
  FaMapMarkerAlt, FaShoppingBag, FaCamera, FaSun, FaCloudRain, FaRoute,
  FaSpa, FaPaw, FaSeedling, FaGlassCheers, FaFire, FaSnowflake,
  FaUmbrellaBeach, FaAppleAlt, FaBaby, FaWalking, FaMoneyBillWave, FaStar,
} from "react-icons/fa"

/**
 * Destination-type icon system.
 *
 * Each place type gets its own icon + label + colour chip, so a map pin or
 * card can show what a place actually IS (a temple, a waterfall, a lake…)
 * instead of a generic location pin.
 *
 * Matching order per destination:
 *   1. name keywords (most reliable — category labels in the catalogue are
 *      noisy for many records),
 *   2. category_name / category string,
 *   3. generic pin fallback.
 */

const TYPES = [
  {
    key: "waterfall",
    Icon: FaWater,
    label: "Waterfall",
    chip: "bg-cyan-100 text-cyan-900",
    emoji: "💦",
    pin: "#0891B2",
    keywords: ["falls", "fall", "jhulpha", "devis", "dhulighat", "suryagandaki", "rudi", "gosaikunda fall", "kunjun", "bardiya fall"],
  },
  {
    key: "lake",
    Icon: FaWater,
    label: "Lake",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🌊",
    pin: "#0284C7",
    keywords: ["lake", "phewa", "rara", "tilicho", "gosaikunda", "tashikhun", "pekwash", "tarsapani"],
  },
  {
    key: "hot_springs",
    Icon: FaSpa,
    label: "Hot Springs",
    chip: "bg-rose-100 text-rose-900",
    emoji: "♨️",
    pin: "#E11D48",
    keywords: ["hot spring", "hotspring", "tarsapani", "bhattapure", "kaski spa"],
  },
  {
    key: "temple_hindu",
    Icon: FaGopuram,
    label: "Hindu Temple",
    chip: "bg-orange-100 text-orange-900",
    emoji: "🛕",
    pin: "#EA580C",
    keywords: ["temple", "mandir", "mandira", "mandir", "pashupatinath", "pashupati", "swayambhu", "boudha", "boudhanath", "kasthamandap", "tal barahi", "barahi", "chharghat", "chhargo", "shivapuri", "nagkotha", "changu narayan", "nagadevta", "deusi", "mukti", "patal chhango", "devis fall"],
  },
  {
    key: "stupa",
    Icon: FaLandmark,
    label: "Stupa",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🕉️",
    pin: "#D97706",
    keywords: ["stupa", "boudhanath", "boudha", "svayambhu", "swayambhunath", "swayambhu", "janakpur dham", "ruru", "rukun"],
  },
  {
    key: "monastery",
    Icon: FaMosque,
    label: "Monastery / Gumba",
    chip: "bg-indigo-100 text-indigo-900",
    emoji: "🏯",
    pin: "#4F46E5",
    keywords: ["monastery", "gumba", "gompa", "kumbhu", "thikhang", "tashiding", "rumtek", "dodran", "saka"],
  },
  {
    key: "church",
    Icon: FaChurch,
    label: "Church",
    chip: "bg-blue-100 text-blue-900",
    emoji: "⛪",
    pin: "#2563EB",
    keywords: ["church", "cathedral", "monastery church"],
  },
  {
    key: "heritage",
    Icon: FaLandmark,
    label: "Heritage Site",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🏛️",
    pin: "#B45309",
    keywords: ["heritage", "palace", "durbar", "fort", "kot ", "koth", "citadel", "bazaar heritage", "munici", "hanumandok", "patan", "bhaktapur", "bhaktapur durbar", "chandragiri"],
  },
  {
    key: "museum",
    Icon: FaTheaterMasks,
    label: "Museum / Gallery",
    chip: "bg-purple-100 text-purple-900",
    emoji: "🖼️",
    pin: "#7C3AED",
    keywords: ["museum", "gallery", "art centre", "art center", "memorial"],
  },
  {
    key: "mountain",
    Icon: FaMountain,
    label: "Mountain / Peak",
    chip: "bg-slate-100 text-slate-900",
    emoji: "🏔️",
    pin: "#334155",
    keywords: ["peak", " summit", " himal", "himalaya", "everest", "annapurna", "langtang", "dhaulagiri", "manaslu", "makalu", "kanchenjunga", "mt. ", "mount ", "tengboche", "namche", "lalabazar"],
  },
  {
    key: "viewpoint",
    Icon: FaCamera,
    label: "Viewpoint",
    chip: "bg-emerald-100 text-emerald-900",
    emoji: "📸",
    pin: "#059669",
    keywords: ["view point", "viewpoint", "view point", "lookout", "look out", "sarangkot", "machhapuchhre base", "chinle", "chipledhunga", "milke", "myanglung", "tinjure", "godawari", "sunrise point"],
  },
  {
    key: "trekking",
    Icon: FaHiking,
    label: "Trekking Trail",
    chip: "bg-lime-100 text-lime-900",
    emoji: "🥾",
    pin: "#65A30D",
    keywords: ["trek", "trail", "teahouse", "base camp", "basecamp", "ridge", "hiking"],
  },
  {
    key: "hills",
    Icon: FaMountain,
    label: "Hill / Danda",
    chip: "bg-green-100 text-green-900",
    emoji: "⛰️",
    pin: "#16A34A",
    keywords: ["danda", "hills", "hill station", "hill ", "bunga", "bunga danda", "surya danda"],
  },
  {
    key: "cave",
    Icon: FaMapMarkerAlt,
    label: "Cave",
    chip: "bg-stone-100 text-stone-900",
    emoji: "🦇",
    pin: "#57534E",
    keywords: ["cave", "caves", "gufi", "gufa", "karnali cave"],
  },
  {
    key: "park",
    Icon: FaTree,
    label: "Park / Garden",
    chip: "bg-green-100 text-green-900",
    emoji: "🌳",
    pin: "#15803D",
    keywords: ["park", "garden", "national park", "botanical", "sanepa", "gardens"],
  },
  {
    key: "wildlife",
    Icon: FaPaw,
    label: "Wildlife / Safari",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🦏",
    pin: "#CA8A04",
    keywords: ["wildlife", "safari", "conservation", "chitwan", "bardiya", "shuklaphanta", "project tiger", "rhino"],
  },
  {
    key: "forest",
    Icon: FaSeedling,
    label: "Forest",
    chip: "bg-green-100 text-green-900",
    emoji: "🌲",
    pin: "#166534",
    keywords: ["forest", "jungle", "shivalik forest", "riverine forest"],
  },
  {
    key: "river",
    Icon: FaRoute,
    label: "River / Rafting",
    chip: "bg-cyan-100 text-cyan-900",
    emoji: "🚣",
    pin: "#0E7490",
    keywords: ["river", "rafting", "rapids", "seti", "bagmati river", "trishuli", "sunkoshi", "gandaki river", "kosi river", "tubing"],
  },
  {
    key: "water_sports",
    Icon: FaUmbrellaBeach,
    label: "Water Sports",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🪂",
    pin: "#0284C7",
    keywords: ["paragliding", "paraglide", "bungee", "zorb", "jet boat", "water sport"],
  },
  {
    key: "camping",
    Icon: FaCampground,
    label: "Camping",
    chip: "bg-lime-100 text-lime-900",
    emoji: "⛺",
    pin: "#4D7C0F",
    keywords: ["camp", "camping", "glamping", "resort camp"],
  },
  {
    key: "food",
    Icon: FaUtensils,
    label: "Food & Cuisine",
    chip: "bg-orange-100 text-orange-900",
    emoji: "🍜",
    pin: "#C2410C",
    keywords: ["restaurant", "cafe", "café", "coffee", "chha", "momos", "momo", "biryani", "thakali", "dining", "kitchen", "banquet", "food", "kunda", "chowk food", "street food"],
  },
  {
    key: "tea_coffee",
    Icon: FaSeedling,
    label: "Tea / Coffee Gardens",
    chip: "bg-green-100 text-green-900",
    emoji: "☕",
    pin: "#16A34A",
    keywords: ["tea garden", "tea estate", "tea factory", "coffee farm", "tea & coffee"],
  },
  {
    key: "orchard",
    Icon: FaAppleAlt,
    label: "Fruit Orchard",
    chip: "bg-rose-100 text-rose-900",
    emoji: "🥭",
    pin: "#E11D48",
    keywords: ["orchard", "mango", "apple farm", "budi", "citrus"],
  },
  {
    key: "hotel",
    Icon: FaHotel,
    label: "Hotel / Lodge",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🏨",
    pin: "#0369A1",
    keywords: ["hotel", "lodge", "resort", "inn ", "guest house", "guesthouse", "hostel", "banquet and party", "palace hotel"],
  },
  {
    key: "village",
    Icon: FaMapMarkerAlt,
    label: "Village",
    chip: "bg-stone-100 text-stone-900",
    emoji: "🏘️",
    pin: "#78716C",
    keywords: ["village", "vill.", "community", "homestay", "newa", "tharu"],
  },
  {
    key: "festival",
    Icon: FaFire,
    label: "Festival / Event",
    chip: "bg-rose-100 text-rose-900",
    emoji: "🎉",
    pin: "#DB2777",
    keywords: ["festival", "mela", "fair", "event", "ceremony", "dashain", "tihar", "holi", "ratha", "jatra"],
  },
  {
    key: "market",
    Icon: FaShoppingBag,
    label: "Market / Bazaar",
    chip: "bg-pink-100 text-pink-900",
    emoji: "🛍️",
    pin: "#BE185D",
    keywords: ["market", "bazaar", "souk", "shopping", "handicraft", "bazar"],
  },
  {
    key: "shopping",
    Icon: FaShoppingBag,
    label: "Shopping",
    chip: "bg-pink-100 text-pink-900",
    emoji: "🛍️",
    pin: "#BE185D",
    keywords: ["shopping", "store", "mall", "boutique", "pashmina"],
  },
  {
    key: "snow",
    Icon: FaSnowflake,
    label: "Snow / Winter",
    chip: "bg-sky-100 text-sky-900",
    emoji: "❄️",
    pin: "#0EA5E9",
    keywords: ["snow", "skiing", "winter", "heli", "glacier"],
  },
  {
    key: "sunset",
    Icon: FaSun,
    label: "Sunrise / Sunset Point",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🌅",
    pin: "#F59E0B",
    keywords: ["sunset", "sunrise", "sun set", "sun rise"],
  },
  {
    key: "rain_water",
    Icon: FaCloudRain,
    label: "Rain / Weather Spot",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🌧️",
    pin: "#0284C7",
    keywords: ["rain", "monsoon", "cloud sea", "clouds sea"],
  },
  {
    key: "walking",
    Icon: FaWalking,
    label: "Walking / Cycling",
    chip: "bg-emerald-100 text-emerald-900",
    emoji: "🚶",
    pin: "#047857",
    keywords: ["walking", "cycling", "cycle", "mountain bike", "scenic drive", "road trip"],
  },
  {
    key: "family",
    Icon: FaBaby,
    label: "Family Spot",
    chip: "bg-rose-100 text-rose-900",
    emoji: "👨‍👩‍",
    pin: "#E11D48",
    keywords: ["family", "kids", "playground", "zoo"],
  },
  {
    key: "celebration",
    Icon: FaGlassCheers,
    label: "Party / Celebration",
    chip: "bg-purple-100 text-purple-900",
    emoji: "",
    pin: "#9333EA",
    keywords: ["party", "club", "nightlife", "bar ", "pub"],
  },
  {
    key: "money",
    Icon: FaMoneyBillWave,
    label: "Bank / ATM",
    chip: "bg-green-100 text-green-900",
    emoji: "💴",
    pin: "#15803D",
    keywords: ["bank", "atm", "exchange"],
  },
  {
    key: "attraction",
    Icon: FaStar,
    label: "Tourist Attraction",
    chip: "bg-emerald-100 text-emerald-900",
    emoji: "⭐",
    pin: "#D97706",
    keywords: ["attraction", "sight", "tourist site", "tourism site"],
  },
]

// Category-name (catalogue label) -> type key, used when the name alone
// doesn't identify the place.
const CATEGORY_HINTS = {
  waterfall: "waterfall",
  waterfalls: "waterfall",
  lake: "lake",
  lakes: "lake",
  "hot springs": "hot_springs",
  temple: "temple_hindu",
  "temples & hindu sites": "temple_hindu",
  pilgrimage: "temple_hindu",
  buddhist: "monastery",
  "buddhist sites & monasteries": "monastery",
  monastery: "monastery",
  gumba: "monastery",
  church: "church",
  heritage: "heritage",
  "unesco & historical heritage": "heritage",
  museum: "museum",
  "museums & galleries": "museum",
  mountain: "mountain",
  "mountains & peaks": "mountain",
  peak: "mountain",
  viewpoint: "viewpoint",
  "viewpoints & lookouts": "viewpoint",
  lookout: "viewpoint",
  trek: "trekking",
  trekking: "trekking",
  hill: "hills",
  "hills & hill stations": "hills",
  cave: "cave",
  caves: "cave",
  park: "park",
  garden: "park",
  "forests & nature": "forest",
  forest: "forest",
  wildlife: "wildlife",
  "wildlife & safari": "wildlife",
  safari: "wildlife",
  river: "river",
  "rivers & river valleys": "river",
  rafting: "river",
  "rafting & water sports": "water_sports",
  "paragliding & air sports": "water_sports",
  camping: "camping",
  "camping & glamping": "camping",
  food: "food",
  "food & culinary tourism": "food",
  "tea & coffee gardens": "tea_coffee",
  "agricultural & farm tourism": "orchard",
  hotel: "hotel",
  village: "village",
  "villages & rural tourism": "village",
  "eco & community tourism": "village",
  festival: "festival",
  "festivals & events": "festival",
  shopping: "market",
  "shopping & handicrafts": "market",
  "snow & winter tourism": "snow",
  "spiritual & wellness": "hot_springs",
  "cultural & ethnic tourism": "heritage",
  "bird watching": "wildlife",
  "road trips & scenic drives": "walking",
  "cycling & mountain biking": "walking",
  "city tourism": "attraction",
  attraction: "attraction",
  valley: "attraction",
  valleys: "attraction",
  "natural wonders": "attraction",
}

const GENERIC = {
  key: "place",
  Icon: FaMapMarkerAlt,
  label: "Place",
  chip: "bg-gray-100 text-gray-900",
  emoji: "📍",
  pin: "#D97706",
}

const byKey = Object.fromEntries(TYPES.map((t) => [t.key, t]))

function nameMatch(name) {
  const n = ` ${String(name || "").toLowerCase()} `
  for (const t of TYPES) {
    for (const kw of t.keywords) {
      if (n.includes(kw)) return t
    }
  }
  return null
}

function categoryMatch(categoryName) {
  const c = String(categoryName || "").trim().toLowerCase()
  if (!c) return null
  // exact catalogue label first
  if (CATEGORY_HINTS[c]) return byKey[CATEGORY_HINTS[c]]
  for (const [label, key] of Object.entries(CATEGORY_HINTS)) {
    if (c === label || c.startsWith(label)) return byKey[key]
  }
  return null
}

/**
 * Resolve the icon/label/chip for a destination-shaped object.
 * Accepts any of: { name, category_name, category, type } where category may
 * be an FK id (ignored) or a name string (used).
 */
export function getPlaceTypeIcon(destination) {
  if (!destination) return GENERIC
  const found =
    nameMatch(destination.name) ||
    categoryMatch(destination.category_name) ||
    categoryMatch(typeof destination.category === "string" ? destination.category : null)
  return found || GENERIC
}

/** Convenience: icon component + classes for JSX. */
export function placeTypeChipClasses(type) {
  return type?.chip || GENERIC.chip
}

export const PLACE_TYPES = TYPES
