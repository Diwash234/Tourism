// src/utils/constants.js

// -----------------------------------------
// Application
// -----------------------------------------
export const APP_NAME =
  import.meta.env.VITE_APP_NAME || "Digital Nepal"

// -----------------------------------------
// Map Configuration
// -----------------------------------------
export const MAP_TILE_URL =
  import.meta.env.VITE_MAP_TILE_URL ||
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

export const MAPILLARY_ACCESS_TOKEN =
  import.meta.env.VITE_MAPILLARY_ACCESS_TOKEN || ""

export const DEFAULT_MAP_CENTER = {
  lat: 28.2096,
  lng: 83.9856,
}

// -----------------------------------------
// User Roles
// -----------------------------------------
export const USER_ROLES = [
  { value: "tourist", label: "Tourist" },
  { value: "guide", label: "Local Guide" },
  { value: "staff", label: "Staff" },
  { value: "hotel_manager", label: "Hotel Manager" },
  { value: "tourist_police", label: "Tourist Police" },
  { value: "police", label: "Police" },
  { value: "hospital_staff", label: "Hospital Staff" },
  { value: "rescue_team", label: "Rescue Team" },
  { value: "emergency_operator", label: "Emergency Operator" },
  { value: "content_moderator", label: "Content Moderator" },
  { value: "district_manager", label: "District Manager" },
  { value: "tourism_admin", label: "Tourism Admin" },
  { value: "admin", label: "Admin" },
  { value: "super_admin", label: "Super Admin" },
]

// -----------------------------------------
// Risk Levels
// -----------------------------------------
export const RISK_LEVELS = {
  LOW: {
    label: "Low",
    color: "bg-forest-50 text-forest-600",
    badge: "badge-risk-low",
  },

  MODERATE: {
    label: "Moderate",
    color: "bg-saffron-50 text-saffron-700",
    badge: "badge-risk-medium",
  },

  // Kept for compatibility with existing components
  MEDIUM: {
    label: "Medium",
    color: "bg-saffron-50 text-saffron-700",
    badge: "badge-risk-medium",
  },

  HIGH: {
    label: "High",
    color: "bg-nepalred-50 text-nepalred-600",
    badge: "badge-risk-high",
  },
}

// -----------------------------------------
// API Configuration
// -----------------------------------------
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api"

// -----------------------------------------
// Pagination
// -----------------------------------------
export const PAGE_SIZE = 12

// -----------------------------------------
// Main Navigation
// -----------------------------------------
export const NAV_LINKS = [
  { label: "Destinations", path: "/destinations" },
  { label: "Budget Planner", path: "/budget-estimator" },
  { label: "Itinerary", path: "/itinerary" },
  { label: "Risk Analysis", path: "/risk-alerts" },
  { label: "Navigation", path: "/navigation" },
  { label: "Emergency", path: "/emergency" },
  { label: "Translation", path: "/translation" },
]

// -----------------------------------------
// Authenticated User Navigation
// -----------------------------------------
export const USER_NAV_LINKS = [
  { label: "Favorites", path: "/favorites" },
  { label: "Notifications", path: "/notifications" },
  { label: "Settings", path: "/settings" },
]