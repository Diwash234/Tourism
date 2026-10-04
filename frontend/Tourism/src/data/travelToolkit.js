/**
 * Travel Toolkit registry — the single source of truth for every traveller-facing
 * tool in the product.
 *
 * Why a data file instead of JSX: the hub groups, filters, ranks and counts these
 * entries, so they have to be plain data. Adding a tool to the app means adding one
 * object here — the hub, the "recommended for you" ranking and the stats row all
 * pick it up with no further wiring.
 *
 * Fields:
 *   id        stable key (used for favourites + recents; never rename, only retire)
 *   path      real route — every path here must exist in App.jsx
 *   label     short noun the traveller recognises
 *   blurb     one honest line about what the tool actually does
 *   category  one of TOOLKIT_CATEGORIES[].id
 *   tags      search synonyms (typos, "taxi", "visa", "SOS" …) so find-as-you-type works
 *   minutes   rough time to get value out of it (drives the "quick win" chip)
 *   popular   boosted in the recommendation ranking
 *   authOnly  only offered to a signed-in traveller
 *   live      backed by a live service (weather, risk, routing) rather than a form
 */

import {
  FiMap, FiCompass, FiDollarSign, FiShield, FiMessageCircle, FiCalendar,
  FiNavigation, FiHeart, FiGrid, FiUsers, FiCamera, FiGlobe, FiPackage,
  FiActivity, FiAlertTriangle, FiPhone, FiBookOpen, FiTrendingUp, FiMapPin,
  FiLayers, FiTool, FiCheckCircle, FiBriefcase, FiTarget, FiZap, FiBookmark,
  FiShare2, FiClock,
} from "react-icons/fi"

export const TOOLKIT_CATEGORIES = [
  { id: "plan", label: "Plan a trip", icon: FiCalendar, blurb: "Build the route, price it, check the paperwork." },
  { id: "explore", label: "Explore places", icon: FiCompass, blurb: "Find where to go and what fits your dates." },
  { id: "navigate", label: "Get around", icon: FiNavigation, blurb: "Directions, distances and what is nearby." },
  { id: "safety", label: "Stay safe", icon: FiShield, blurb: "Live alerts, SOS and family tracking." },
  { id: "money", label: "Money & stays", icon: FiDollarSign, blurb: "Budget, track spend and book a room." },
  { id: "connect", label: "Language & help", icon: FiMessageCircle, blurb: "Translate, ask the assistant, get support." },
  { id: "you", label: "Your trips", icon: FiHeart, blurb: "Everything you have saved, booked and shared.", authOnly: true },
]

export const TOOLKIT_TOOLS = [
  // ---- Plan ----
  { id: "itinerary", path: "/itinerary", label: "Trip planner", category: "plan", icon: FiCalendar, popular: true, minutes: 10,
    blurb: "Day-by-day itinerary with hotels, hospitals and police ranked by distance.",
    tags: ["itinerary", "plan", "days", "route", "schedule", "trip"] },
  { id: "budget-estimator", path: "/budget-estimator", label: "Budget estimator", category: "plan", icon: FiDollarSign, popular: true, minutes: 3, live: true,
    blurb: "ML-backed daily budget in NPR and USD for your travel style.",
    tags: ["budget", "cost", "price", "money", "npr", "usd", "estimate", "expense"] },
  { id: "compare", path: "/compare", label: "Compare places", category: "plan", icon: FiLayers, minutes: 4,
    blurb: "Put two or three destinations side by side on price, weather and risk.",
    tags: ["compare", "versus", "vs", "difference", "which", "better"] },
  { id: "decide", path: "/decide", label: "Which should I choose?", category: "plan", icon: FiTarget, minutes: 2,
    blurb: "Answer a few questions and get a shortlist that matches them.",
    tags: ["decide", "choose", "pick", "recommend", "suggest", "undecided"] },
  { id: "before-you-travel", path: "/before-you-travel", label: "Visa, permits & fees", category: "plan", icon: FiBookOpen, minutes: 5,
    blurb: "Visa rules, TIMS, park fees and altitude advice with source links.",
    tags: ["visa", "permit", "tims", "passport", "fee", "entry", "paperwork", "document"] },
  { id: "packages", path: "/packages", label: "Travel packages", category: "plan", icon: FiPackage, minutes: 6,
    blurb: "Fixed itineraries from licensed operators, priced and dated.",
    tags: ["package", "tour", "deal", "operator", "book", "bundle"] },
  { id: "travel-planner", path: "/travel", label: "Travel planner", category: "plan", icon: FiTool, minutes: 8,
    blurb: "Multi-stop planning with transport legs between cities.",
    tags: ["planner", "multi stop", "transport", "legs", "city"] },
  { id: "submit-place", path: "/destinations/submit", label: "Add a place", category: "plan", icon: FiMapPin, minutes: 6,
    blurb: "Submit a destination or trail the map is missing.",
    tags: ["submit", "add", "contribute", "new place", "missing", "correction"] },

  // ---- Explore ----
  { id: "destinations", path: "/destinations", label: "All destinations", category: "explore", icon: FiMap, popular: true, minutes: 5,
    blurb: "Every recorded place in Nepal, filtered by category, province and budget.",
    tags: ["destinations", "places", "list", "browse", "search", "attractions"] },
  { id: "discover", path: "/discover", label: "Find by activity", category: "explore", icon: FiActivity, minutes: 3,
    blurb: "Trekking, lakes, temples, wildlife — start from what you want to do.",
    tags: ["activity", "trek", "hike", "temple", "lake", "wildlife", "category", "things to do"] },
  { id: "discover-nepal", path: "/discover-nepal", label: "Discover Nepal", category: "explore", icon: FiGlobe, minutes: 6,
    blurb: "A guided tour through regions, seasons and highlights.",
    tags: ["discover", "regions", "season", "highlights", "overview", "tour"] },
  { id: "explore-map", path: "/explore-map", label: "Explore by province", category: "explore", icon: FiMap, minutes: 7,
    blurb: "Browse the whole country on a map, province by province.",
    tags: ["map", "province", "province", "region", "atlas", "geography"] },
  { id: "districts", path: "/districts", label: "Districts & provinces", category: "explore", icon: FiGrid, minutes: 5,
    blurb: "All 77 districts with destination counts and emergency contacts.",
    tags: ["district", "province", "77", "admin", "county", "region"] },
  { id: "gallery", path: "/gallery", label: "Photo gallery", category: "explore", icon: FiCamera, minutes: 4,
    blurb: "Verified photography from the database, newest first.",
    tags: ["gallery", "photos", "images", "pictures", "pic"] },
  { id: "recommendation", path: "/recommendation", label: "Recommended for you", category: "explore", icon: FiZap, popular: true, minutes: 2, live: true,
    blurb: "Personalised picks from the recommendation model.",
    tags: ["recommend", "personalised", "suggested", "for me", "ml", "ai"] },
  { id: "hotels-search", path: "/hotels/search", label: "Find hotels", category: "explore", icon: FiBriefcase, popular: true, minutes: 5,
    blurb: "Search stays by city, price and verified status.",
    tags: ["hotel", "stay", "lodge", "room", "accommodation", "sleep", "hostel"] },

  // ---- Navigate ----
  { id: "navigation", path: "/navigation", label: "Turn-by-turn navigation", category: "navigate", icon: FiNavigation, popular: true, minutes: 4, live: true,
    blurb: "Road routes with maneuver grades and honest fallback labelling.",
    tags: ["navigation", "directions", "drive", "turn by turn", "gps", "route", "wayfinding"] },
  { id: "distances", path: "/distances", label: "Distances & fares", category: "navigate", icon: FiTrendingUp, minutes: 3,
    blurb: "Distance, travel time and taxi fare between any two places.",
    tags: ["distance", "fare", "taxi", "how far", "duration", "travel time", "km"] },
  { id: "nearby-places", path: "/nearby-places", label: "What is nearby", category: "navigate", icon: FiCompass, popular: true, minutes: 2, live: true,
    blurb: "Hospitals, pharmacies, banks and police sorted by distance from you.",
    tags: ["nearby", "close", "around me", "hospital", "pharmacy", "bank", "police", "atm", "poi"] },
  { id: "map", path: "/explore-map", label: "Interactive map", category: "navigate", icon: FiMapPin, minutes: 6,
    blurb: "Full-screen map with places, transit and satellite imagery.",
    tags: ["map", "satellite", "transit", "visual", "pan"] },

  // ---- Safety ----
  { id: "safety", path: "/safety", label: "Safety centre", category: "safety", icon: FiShield, popular: true, minutes: 4, live: true,
    blurb: "Risk score, current hazards and what is safe to do today.",
    tags: ["safety", "risk", "danger", "hazard", "secure", "safe", "advisory"] },
  { id: "risk-alerts", path: "/risk-alerts", label: "Live risk alerts", category: "safety", icon: FiAlertTriangle, popular: true, minutes: 2, live: true,
    blurb: "Official and community alerts with severity and expiry times.",
    tags: ["alert", "warning", "risk", "advisory", "notice", "disaster", "flood", "strike"] },
  { id: "emergency", path: "/emergency", label: "Emergency & SOS", category: "safety", icon: FiPhone, popular: true, minutes: 1, live: true,
    blurb: "One-tap SOS, national hotlines and nearby hospitals.",
    tags: ["emergency", "sos", "help", "police", "ambulance", "fire", "hotline", "urgent", "call"] },
  { id: "family-safety", path: "/family-safety", label: "Family safety", category: "safety", icon: FiUsers, minutes: 5,
    blurb: "Share your live location and check on travelling family.",
    tags: ["family", "share", "location", "track", "kids", "parents", "group"] },
  { id: "shared-trip", path: "/safety/shared/new", label: "Share a live trip", category: "safety", icon: FiShare2, minutes: 2,
    blurb: "Send a link so others can follow your journey as it happens.",
    tags: ["share", "live", "link", "track", "follow", "trip link"] },

  // ---- Money ----
  { id: "expenditure", path: "/expenditure", label: "Track my spending", category: "money", icon: FiActivity, minutes: 3,
    blurb: "Log what you actually spent and compare it to the estimate.",
    tags: ["spend", "expense", "money", "log", "actual", "receipt", "budget actual"] },
  { id: "my-bookings", path: "/my-bookings", label: "My bookings", category: "money", icon: FiBookmark, minutes: 2, authOnly: true,
    blurb: "Hotel and package reservations with their current status.",
    tags: ["booking", "reservation", "hotel", "order", "invoice", "stay"] },
  { id: "favorites", path: "/favorites", label: "Saved places", category: "money", icon: FiHeart, minutes: 2, authOnly: true,
    blurb: "Everything you starred, in one shortlist.",
    tags: ["saved", "favourites", "favorites", "starred", "wishlist", "shortlist"] },
  { id: "checkout", path: "/checkout", label: "Checkout", category: "money", icon: FiDollarSign, minutes: 4,
    blurb: "Pay for a package or booking and get your reference.",
    tags: ["checkout", "pay", "payment", "card", "wallet", "confirm"] },

  // ---- Connect ----
  { id: "translation", path: "/translation", label: "Live translation", category: "connect", icon: FiGlobe, popular: true, minutes: 2, live: true,
    blurb: "Translate a conversation in Nepali, Hindi, English and more.",
    tags: ["translate", "language", "nepali", "hindi", "speak", "conversation", "speech"] },
  { id: "phrasebook", path: "/language", label: "Phrasebook", category: "connect", icon: FiBookOpen, minutes: 3,
    blurb: "Essential phrases with audio, grouped by situation.",
    tags: ["phrase", "phrasebook", "say", "speak", "audio", "words", "conversation"] },
  { id: "chatbot", path: "/chatbot", label: "Himal AI assistant", category: "connect", icon: FiMessageCircle, popular: true, minutes: 3, live: true,
    blurb: "Ask anything about your trip and get an answer with sources.",
    tags: ["chat", "assistant", "ai", "ask", "help", "question", "bot", "himal"] },
  { id: "support", path: "/support", label: "Help & support", category: "connect", icon: FiPhone, minutes: 5,
    blurb: "Contact the team, report a problem or find an answer.",
    tags: ["help", "support", "contact", "report", "issue", "faq", "problem"] },
  { id: "guides", path: "/guides", label: "Licensed guides", category: "connect", icon: FiUsers, minutes: 4,
    blurb: "Find and compare registered guides with their languages.",
    tags: ["guide", "porter", "instructor", "hire", "translator", "local"] },

  // ---- You ----
  { id: "dashboard", path: "/dashboard", label: "My dashboard", category: "you", icon: FiGrid, authOnly: true, minutes: 2,
    blurb: "Your trips, notifications and activity at a glance.",
    tags: ["dashboard", "overview", "home", "summary", "account"] },
  { id: "history", path: "/history", label: "Visit history", category: "you", icon: FiClock, authOnly: true, minutes: 2,
    blurb: "Places you viewed and searched, so you can pick them back up.",
    tags: ["history", "recent", "viewed", "visited", "timeline", "activity"] },
  { id: "notifications", path: "/notifications", label: "Notifications", category: "you", icon: FiAlertTriangle, authOnly: true, minutes: 1, live: true,
    blurb: "Booking updates, alerts and system messages.",
    tags: ["notification", "inbox", "alert", "message", "update"] },
  { id: "my-submissions", path: "/my-submissions", label: "My submissions", category: "you", icon: FiCheckCircle, authOnly: true, minutes: 3,
    blurb: "Track the places and services you submitted through review.",
    tags: ["submission", "pending", "review", "approved", "contribution", "status"] },
  { id: "settings", path: "/settings", label: "Settings", category: "you", icon: FiTool, authOnly: true, minutes: 4,
    blurb: "Language, notifications, privacy and account preferences.",
    tags: ["settings", "preferences", "account", "privacy", "language", "theme"] },
  { id: "profile", path: "/profile", label: "My profile", category: "you", icon: FiUsers, authOnly: true, minutes: 3,
    blurb: "Your details, verification status and public bio.",
    tags: ["profile", "account", "details", "avatar", "bio", "personal"] },
]

/** Flat id -> tool lookup, built once at module load. */
export const TOOL_BY_ID = Object.fromEntries(TOOLKIT_TOOLS.map((tool) => [tool.id, tool]))

export const TOOLKIT_CATEGORY_BY_ID = Object.fromEntries(TOOLKIT_CATEGORIES.map((cat) => [cat.id, cat]))

/** Categories that actually contain at least one visible tool. */
export const usedToolkitCategories = (authOnly) =>
  TOOLKIT_CATEGORIES.filter(
    (cat) =>
      (!cat.authOnly || authOnly) &&
      TOOLKIT_TOOLS.some((tool) => tool.category === cat.id && (!tool.authOnly || authOnly))
  )
