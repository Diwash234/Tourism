export const APP_NAME = import.meta.env.VITE_APP_NAME || "Digital Nepal"

export const PAGE_SIZE = 9

export const MAP_TILE_URL =
  import.meta.env.VITE_MAP_TILE_URL ||
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

export const MAPILLARY_ACCESS_TOKEN =
  import.meta.env.VITE_MAPILLARY_ACCESS_TOKEN || ""

export const DEFAULT_MAP_CENTER = { lat: 28.2096, lng: 83.9856 } // Pokhara

// FIXED: this used generic Tailwind green/yellow/red, completely
// bypassing the Nepal color system — meaning AlertCard.jsx showed
// generic colors for the exact same risk concept that RiskCard.jsx (a
// separate badge-risk-* class system in index.css) already shows in
// Nepal forest/saffron/nepalred. Aligned here so both paths match.
export const RISK_LEVELS = {
  LOW: { label: "Low", color: "bg-forest-50 text-forest-600" },
  MODERATE: { label: "Moderate", color: "bg-saffron-50 text-saffron-700" },
  HIGH: { label: "High", color: "bg-nepalred-50 text-nepalred-600" },
}

export const NAV_LINKS = [
  { label: "Destinations", path: "/destinations" },
  { label: "Budget Planner", path: "/budget-estimator" },
  { label: "Risk Analysis", path: "/risk-alerts" },
  { label: "Navigation", path: "/navigation" },
  { label: "Emergency", path: "/emergency" },
  { label: "Translation", path: "/translation" },
]

// Shown only to authenticated users, usually as icon links / a dropdown
export const USER_NAV_LINKS = [
  { label: "Favorites", path: "/favorites" },
  { label: "Notifications", path: "/notifications" },
  { label: "Settings", path: "/settings" },
]