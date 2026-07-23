export const APP_NAME = import.meta.env.VITE_APP_NAME || "Tourist"

export const MAP_TILE_URL =
  import.meta.env.VITE_MAP_TILE_URL ||
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

export const DEFAULT_MAP_CENTER = { lat: 28.2096, lng: 83.9856 } // Pokhara

export const RISK_LEVELS = {
  LOW: { label: "Low", color: "bg-green-100 text-green-700" },
  MODERATE: { label: "Moderate", color: "bg-yellow-100 text-yellow-700" },
  HIGH: { label: "High", color: "bg-red-100 text-red-700" },
}

export const NAV_LINKS = [
  { label: "Home", path: "/" },
  { label: "Destinations", path: "/destinations" },
  { label: "About", path: "/about" },
  { label: "Contact", path: "/contact" },
]

// Languages spoken across Nepal's regions, used by the Translation page and
// destination language tags. code follows ISO 639 where available.
export const NEPAL_LANGUAGES = [
  { code: "ne", label: "Nepali", native: "नेपाली" },
  { code: "mai", label: "Maithili", native: "मैथिली" },
  { code: "bho", label: "Bhojpuri", native: "भोजपुरी" },
  { code: "thq", label: "Tharu", native: "थारू" },
  { code: "taj", label: "Tamang", native: "तामाङ" },
  { code: "new", label: "Newari (Nepal Bhasa)", native: "नेपाल भाषा" },
  { code: "mgp", label: "Magar", native: "मगर" },
  { code: "bjj", label: "Bajjika", native: "बज्जिका" },
  { code: "awa", label: "Awadhi", native: "अवधी" },
  { code: "gvr", label: "Gurung", native: "गुरुङ" },
  { code: "lif", label: "Limbu", native: "लिम्बू" },
  { code: "bap", label: "Rai (Kirati)", native: "राई" },
  { code: "xsr", label: "Sherpa", native: "शेर्पा" },
  { code: "dty", label: "Doteli", native: "डोटेली" },
  { code: "rjb", label: "Rajbanshi", native: "राजवंशी" },
  { code: "urd", label: "Urdu", native: "اردو" },
]

// Widely used international languages, shown alongside the Nepal-specific list
export const INTERNATIONAL_LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "zh", label: "Chinese", native: "中文" },
  { code: "fr", label: "French", native: "Français" },
  { code: "es", label: "Spanish", native: "Español" },
  { code: "ja", label: "Japanese", native: "日本語" },
  { code: "de", label: "German", native: "Deutsch" },
  { code: "ar", label: "Arabic", native: "العربية" },
  { code: "ru", label: "Russian", native: "Русский" },
  { code: "pt", label: "Portuguese", native: "Português" },
  { code: "ko", label: "Korean", native: "한국어" },
]

// Regional / local languages of India, commonly needed by travelers moving between
// Nepal and India border regions, or visiting from India.
export const INDIA_LANGUAGES = [
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "ur", label: "Urdu", native: "اردو" },
  { code: "pa", label: "Punjabi", native: "ਪੰਜਾਬੀ" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ml", label: "Malayalam", native: "മലയാളം" },
  { code: "or", label: "Odia", native: "ଓଡ଼ିଆ" },
  { code: "as", label: "Assamese", native: "অসমীয়া" },
]

// Grouped by country/region — used to render the Translation page as tabs and
// makes it straightforward to add more countries' local languages later.
export const LANGUAGE_GROUPS = [
  { key: "nepal", label: "Nepal", languages: NEPAL_LANGUAGES, theme: "purple" },
  { key: "india", label: "India", languages: INDIA_LANGUAGES, theme: "amber" },
  { key: "international", label: "International", languages: INTERNATIONAL_LANGUAGES, theme: "blue" },
]

export const HERITAGE_CATEGORIES = [
  { label: "UNESCO World Heritage", value: "unesco" },
  { label: "Temple / Religious Site", value: "religious" },
  { label: "Palace / Durbar Square", value: "palace" },
  { label: "Monastery / Gumba", value: "monastery" },
  { label: "Traditional Village", value: "village" },
]

// One-click travel mode presets for the Budget Estimator
export const TRAVEL_MODES = [
  { value: "flight", label: "Flight", icon: "FiSend" },
  { value: "bus", label: "Bus", icon: "FiTruck" },
  { value: "car", label: "Private Car", icon: "FiTruck" },
  { value: "train", label: "Train", icon: "FiTruck" },
  { value: "bike", label: "Bike / Scooter", icon: "FiTruck" },
  { value: "walking", label: "Walking / Trekking", icon: "FiTruck" },
]

// One-click trip-length presets for the Budget Estimator
export const DURATION_PRESETS = [
  { label: "Weekend (2 days)", days: 2 },
  { label: "Short Trip (5 days)", days: 5 },
  { label: "One Week", days: 7 },
  { label: "Two Weeks", days: 14 },
]

// Booking package tiers offered on the Packages page
export const PACKAGE_TIERS = [
  {
    key: "silver",
    label: "Silver",
    priceMultiplier: 1,
    color: "from-gray-400 to-gray-500",
    perks: ["Standard hotel (3-star)", "Shared transport", "Local guide (group)", "Breakfast included"],
  },
  {
    key: "gold",
    label: "Gold",
    priceMultiplier: 1.6,
    color: "from-amber-400 to-amber-600",
    perks: ["Premium hotel (4-star)", "Private transport", "Dedicated local guide", "All meals included", "1 free activity"],
  },
  {
    key: "platinum",
    label: "Platinum",
    priceMultiplier: 2.4,
    color: "from-indigo-500 to-purple-600",
    perks: ["Luxury hotel (5-star)", "Private car with driver", "Personal guide & translator", "All meals + activities", "Airport pickup & drop"],
  },
]

// Account types available at registration. Note: in production, admin accounts
// should be provisioned by an existing admin rather than self-registered —
// this option is kept here per product requirements but should be gated
// server-side.
export const ROLE_OPTIONS = [
  { value: "user", label: "Traveler", description: "Explore destinations, plan trips and budgets" },
  { value: "local", label: "Local Guide", description: "Showcase your local places with photos" },
  { value: "admin", label: "Admin", description: "Manage the platform and agencies" },
]