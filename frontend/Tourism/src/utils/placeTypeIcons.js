import { createElement } from "react"
import { LOCATION_ICON_URL } from "./locationIcons"

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


// Real icon artwork per place type (Twemoji — Mozilla, CC-BY 4.0). The
// component renders an <img> so every existing <TypeIcon className="…"/>
// call site keeps working; `emoji` is retained only as a text fallback.
const typeIcon = (key, label) =>
  function LocationTypeIcon(props) {
    return createElement("img", {
      src: LOCATION_ICON_URL(key),
      alt: label,
      draggable: false,
      style: { display: "inline-block", objectFit: "contain" },
      ...props,
    })
  }


const TYPES = [
  // Service places come FIRST: their name IS the identity. A "Rudra Resort,
  // Bardiya" is a hotel (not a wildlife spot); "Nepal Bank Limited, Kaski"
  // is a bank (not a market); "Buddha Hospital, Bhaktapur" is a hospital
  // (not a temple). Theme keywords below must never override these.
  {
    key: "hospital",
    Icon: typeIcon("hospital", "Hospital / Clinic"),
    label: "Hospital / Clinic",
    chip: "bg-red-100 text-red-900",
    emoji: "🏥",
    pin: "#DC2626",
    keywords: ["hospital", "clinic", "medical", "health post", "healthpost", "poly clinic", "polyclinic", "ambulance", "dha ", "dhars", "base camp hospital"],
  },
  {
    key: "hotel",
    Icon: typeIcon("hotel", "Hotel / Lodge"),
    label: "Hotel / Lodge",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🏨",
    pin: "#0369A1",
    keywords: ["hotel", "lodge", "resort", "inn ", "guest house", "guesthouse", "hostel", "banquet and party", "palace hotel"],
  },
  {
    key: "money",
    Icon: typeIcon("money", "Bank / ATM"),
    label: "Bank / ATM",
    chip: "bg-green-100 text-green-900",
    emoji: "🏦",
    pin: "#15803D",
    keywords: ["bank", "atm", "exchange"],
  },
  {
    key: "waterfall",
    Icon: typeIcon("waterfall", "Waterfall"),
    label: "Waterfall",
    chip: "bg-cyan-100 text-cyan-900",
    emoji: "💦",
    pin: "#0891B2",
    keywords: ["falls", "fall", "jhulpha", "devis", "dhulighat", "suryagandaki", "rudi", "gosaikunda fall", "kunjun", "bardiya fall"],
  },
  {
    key: "lake",
    Icon: typeIcon("lake", "Lake"),
    label: "Lake",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🌊",
    pin: "#0284C7",
    keywords: ["lake", "phewa", "rara", "tilicho", "gosaikunda", "tashikhun", "pekwash", "tarsapani"],
  },
  {
    key: "hot_springs",
    Icon: typeIcon("hot_springs", "Hot Springs"),
    label: "Hot Springs",
    chip: "bg-rose-100 text-rose-900",
    emoji: "♨️",
    pin: "#E11D48",
    keywords: ["hot spring", "hotspring", "tarsapani", "bhattapure", "kaski spa"],
  },
  {
    key: "temple_hindu",
    Icon: typeIcon("temple_hindu", "Hindu Temple"),
    label: "Hindu Temple",
    chip: "bg-orange-100 text-orange-900",
    emoji: "🛕",
    pin: "#EA580C",
    // NOTE: stupa names (boudhanath, swayambhunath, …) live ONLY in the
    // "stupa" type below — they are Buddhist, not Hindu, and temple matches
    // first in the scan order, so listing them here would mislabel them.
    keywords: ["temple", "mandir", "mandira", "mandir", "pashupatinath", "pashupati", "kasthamandap", "tal barahi", "barahi", "chharghat", "chhargo", "shivapuri", "nagkotha", "changu narayan", "nagadevta", "deusi", "mukti", "patal chhango", "devis fall"],
  },
  {
    key: "stupa",
    Icon: typeIcon("stupa", "Stupa"),
    label: "Stupa",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🕉️",
    pin: "#D97706",
    keywords: ["stupa", "boudhanath", "boudha", "svayambhu", "swayambhunath", "swayambhu", "janakpur dham", "ruru", "rukun"],
  },
  {
    key: "monastery",
    Icon: typeIcon("monastery", "Monastery / Gumba"),
    label: "Monastery / Gumba",
    chip: "bg-indigo-100 text-indigo-900",
    emoji: "🏯",
    pin: "#4F46E5",
    keywords: ["monastery", "gumba", "gompa", "kumbhu", "thikhang", "tashiding", "rumtek", "dodran", "saka"],
  },
  {
    key: "church",
    Icon: typeIcon("church", "Church"),
    label: "Church",
    chip: "bg-blue-100 text-blue-900",
    emoji: "⛪",
    pin: "#2563EB",
    keywords: ["church", "cathedral", "monastery church"],
  },
  {
    key: "heritage",
    Icon: typeIcon("heritage", "Heritage Site"),
    label: "Heritage Site",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🏛️",
    pin: "#B45309",
    keywords: ["heritage", "palace", "durbar", "fort", "kot ", "koth", "citadel", "bazaar heritage", "munici", "hanumandok", "patan", "bhaktapur", "bhaktapur durbar", "chandragiri"],
  },
  {
    key: "museum",
    Icon: typeIcon("museum", "Museum / Gallery"),
    label: "Museum / Gallery",
    chip: "bg-purple-100 text-purple-900",
    emoji: "🖼️",
    pin: "#7C3AED",
    keywords: ["museum", "gallery", "art centre", "art center", "memorial"],
  },
  {
    key: "mountain",
    Icon: typeIcon("mountain", "Mountain / Peak"),
    label: "Mountain / Peak",
    chip: "bg-slate-100 text-slate-900",
    emoji: "🏔️",
    pin: "#334155",
    keywords: ["peak", " summit", " himal", "himalaya", "everest", "annapurna", "langtang", "dhaulagiri", "manaslu", "makalu", "kanchenjunga", "mt. ", "mount ", "tengboche", "namche", "lalabazar"],
  },
  {
    key: "viewpoint",
    Icon: typeIcon("viewpoint", "Viewpoint"),
    label: "Viewpoint",
    chip: "bg-emerald-100 text-emerald-900",
    emoji: "📸",
    pin: "#059669",
    keywords: ["view point", "viewpoint", "view point", "lookout", "look out", "sarangkot", "machhapuchhre base", "chinle", "chipledhunga", "milke", "myanglung", "tinjure", "godawari", "sunrise point"],
  },
  {
    key: "trekking",
    Icon: typeIcon("trekking", "Trekking Trail"),
    label: "Trekking Trail",
    chip: "bg-lime-100 text-lime-900",
    emoji: "🥾",
    pin: "#65A30D",
    keywords: ["trek", "trail", "teahouse", "base camp", "basecamp", "ridge", "hiking"],
  },
  {
    key: "hills",
    Icon: typeIcon("hills", "Hill / Danda"),
    label: "Hill / Danda",
    chip: "bg-green-100 text-green-900",
    emoji: "⛰️",
    pin: "#16A34A",
    keywords: ["danda", "hills", "hill station", "hill ", "bunga", "bunga danda", "surya danda"],
  },
  {
    key: "cave",
    Icon: typeIcon("cave", "Cave"),
    label: "Cave",
    chip: "bg-stone-100 text-stone-900",
    emoji: "🦇",
    pin: "#57534E",
    keywords: ["cave", "caves", "gufi", "gufa", "karnali cave"],
  },
  {
    key: "park",
    Icon: typeIcon("park", "Park / Garden"),
    label: "Park / Garden",
    chip: "bg-green-100 text-green-900",
    emoji: "🌳",
    pin: "#15803D",
    keywords: ["park", "garden", "national park", "botanical", "sanepa", "gardens"],
  },
  {
    key: "wildlife",
    Icon: typeIcon("wildlife", "Wildlife / Safari"),
    label: "Wildlife / Safari",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🦏",
    pin: "#CA8A04",
    keywords: ["wildlife", "safari", "conservation", "chitwan", "bardiya", "shuklaphanta", "project tiger", "rhino"],
  },
  {
    key: "forest",
    Icon: typeIcon("forest", "Forest"),
    label: "Forest",
    chip: "bg-green-100 text-green-900",
    emoji: "🌲",
    pin: "#166534",
    keywords: ["forest", "jungle", "shivalik forest", "riverine forest"],
  },
  {
    key: "river",
    Icon: typeIcon("river", "River / Rafting"),
    label: "River / Rafting",
    chip: "bg-cyan-100 text-cyan-900",
    emoji: "🚣",
    pin: "#0E7490",
    keywords: ["river", "rafting", "rapids", "seti", "bagmati river", "trishuli", "sunkoshi", "gandaki river", "kosi river", "tubing"],
  },
  {
    key: "water_sports",
    Icon: typeIcon("water_sports", "Water Sports"),
    label: "Water Sports",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🪂",
    pin: "#0284C7",
    keywords: ["paragliding", "paraglide", "bungee", "zorb", "jet boat", "water sport"],
  },
  {
    key: "camping",
    Icon: typeIcon("camping", "Camping"),
    label: "Camping",
    chip: "bg-lime-100 text-lime-900",
    emoji: "⛺",
    pin: "#4D7C0F",
    keywords: ["camp", "camping", "glamping", "resort camp"],
  },
  {
    key: "food",
    Icon: typeIcon("food", "Food & Cuisine"),
    label: "Food & Cuisine",
    chip: "bg-orange-100 text-orange-900",
    emoji: "🍜",
    pin: "#C2410C",
    keywords: ["restaurant", "cafe", "café", "coffee", "chha", "momos", "momo", "biryani", "thakali", "dining", "kitchen", "banquet", "food", "kunda", "chowk food", "street food"],
  },
  {
    key: "tea_coffee",
    Icon: typeIcon("tea_coffee", "Tea / Coffee Gardens"),
    label: "Tea / Coffee Gardens",
    chip: "bg-green-100 text-green-900",
    emoji: "☕",
    pin: "#16A34A",
    keywords: ["tea garden", "tea estate", "tea factory", "coffee farm", "tea & coffee"],
  },
  {
    key: "orchard",
    Icon: typeIcon("orchard", "Fruit Orchard"),
    label: "Fruit Orchard",
    chip: "bg-rose-100 text-rose-900",
    emoji: "🥭",
    pin: "#E11D48",
    keywords: ["orchard", "mango", "apple farm", "budi", "citrus"],
  },
  {
    key: "village",
    Icon: typeIcon("village", "Village"),
    label: "Village",
    chip: "bg-stone-100 text-stone-900",
    emoji: "🏘️",
    pin: "#78716C",
    keywords: ["village", "vill.", "community", "homestay", "newa", "tharu"],
  },
  {
    key: "festival",
    Icon: typeIcon("festival", "Festival / Event"),
    label: "Festival / Event",
    chip: "bg-rose-100 text-rose-900",
    emoji: "🎉",
    pin: "#DB2777",
    keywords: ["festival", "mela", "fair", "event", "ceremony", "dashain", "tihar", "holi", "ratha", "jatra"],
  },
  {
    key: "market",
    Icon: typeIcon("market", "Market / Bazaar"),
    label: "Market / Bazaar",
    chip: "bg-pink-100 text-pink-900",
    emoji: "🛍️",
    pin: "#BE185D",
    keywords: ["market", "bazaar", "souk", "shopping", "handicraft", "bazar"],
  },
  {
    key: "shopping",
    Icon: typeIcon("shopping", "Shopping"),
    label: "Shopping",
    chip: "bg-pink-100 text-pink-900",
    emoji: "🛍️",
    pin: "#BE185D",
    keywords: ["shopping", "store", "mall", "boutique", "pashmina"],
  },
  {
    key: "snow",
    Icon: typeIcon("snow", "Snow / Winter"),
    label: "Snow / Winter",
    chip: "bg-sky-100 text-sky-900",
    emoji: "❄️",
    pin: "#0EA5E9",
    keywords: ["snow", "skiing", "winter", "heli", "glacier"],
  },
  {
    key: "sunset",
    Icon: typeIcon("sunset", "Sunrise / Sunset Point"),
    label: "Sunrise / Sunset Point",
    chip: "bg-amber-100 text-amber-900",
    emoji: "🌅",
    pin: "#F59E0B",
    keywords: ["sunset", "sunrise", "sun set", "sun rise"],
  },
  {
    key: "rain_water",
    Icon: typeIcon("rain_water", "Rain / Weather Spot"),
    label: "Rain / Weather Spot",
    chip: "bg-sky-100 text-sky-900",
    emoji: "🌧️",
    pin: "#0284C7",
    keywords: ["rain", "monsoon", "cloud sea", "clouds sea"],
  },
  {
    key: "walking",
    Icon: typeIcon("walking", "Walking / Cycling"),
    label: "Walking / Cycling",
    chip: "bg-emerald-100 text-emerald-900",
    emoji: "🚶",
    pin: "#047857",
    keywords: ["walking", "cycling", "cycle", "mountain bike", "scenic drive", "road trip"],
  },
  {
    key: "family",
    Icon: typeIcon("family", "Family Spot"),
    label: "Family Spot",
    chip: "bg-rose-100 text-rose-900",
    emoji: "👨‍👩‍",
    pin: "#E11D48",
    keywords: ["family", "kids", "playground", "zoo"],
  },
  {
    key: "celebration",
    Icon: typeIcon("celebration", "Party / Celebration"),
    label: "Party / Celebration",
    chip: "bg-purple-100 text-purple-900",
    emoji: "",
    pin: "#9333EA",
    keywords: ["party", "club", "nightlife", "bar ", "pub"],
  },
  {
    key: "attraction",
    Icon: typeIcon("attraction", "Tourist Attraction"),
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
  Icon: typeIcon("pin", "Place"),
  label: "Place",
  chip: "bg-gray-100 text-gray-900",
  emoji: "📍",
  pin: "#D97706",
}

const byKey =  Object.fromEntries(TYPES.map((t) => [t.key, t]))

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


/**
 * Ready-to-render <img> icon for a destination-shaped object.
 * Use this where a plain icon is wanted — never render the type object
 * returned by getPlaceTypeIcon() directly.
 */
export const PlaceTypeIconImg = ({ destination, className, ...rest }) => {
  const type = getPlaceTypeIcon(destination)
  const TypeIcon = type.Icon
  return createElement(TypeIcon, { className, "aria-hidden": "true", ...rest })
}

/** Convenience: icon component + classes for JSX. */
export function placeTypeChipClasses(type) {
  return type?.chip || GENERIC.chip
}

export const PLACE_TYPES = TYPES
