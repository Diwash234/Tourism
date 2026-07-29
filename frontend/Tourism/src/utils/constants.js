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