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
  lng: 83.9856
}



// -----------------------------------------
// Risk Levels
// Used by RiskCard, AlertCard, Risk pages
// -----------------------------------------

export const RISK_LEVELS = {

  LOW: {
    label: "Low",
    color: "bg-forest-50 text-forest-600",
    badge: "badge-risk-low"
  },


  MODERATE: {
    label: "Moderate",
    color: "bg-saffron-50 text-saffron-700",
    badge: "badge-risk-medium"
  },


  MEDIUM: {
    label: "Medium",
    color: "bg-saffron-50 text-saffron-700",
    badge: "badge-risk-medium"
  },


  HIGH: {
    label: "High",
    color: "bg-nepalred-50 text-nepalred-600",
    badge: "badge-risk-high"
  }

}



// -----------------------------------------
// API Configuration
// -----------------------------------------

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000/api"



// -----------------------------------------
// Pagination
// Used by DestinationList.jsx
// -----------------------------------------

export const PAGE_SIZE = 12



// -----------------------------------------
// Navigation Links
// -----------------------------------------

export const NAV_LINKS = [

  {
    label: "Destinations",
    path: "/destinations"
  },

  {
    label: "Budget Planner",
    path: "/budget-estimator"
  },

  {
    label: "Itinerary",
    path: "/itinerary"
  },

  {
    label: "Risk Analysis",
    path: "/risk-alerts"
  },

  {
    label: "Navigation",
    path: "/navigation"
  },

  {
    label: "Emergency",
    path: "/emergency"
  },

  {
    label: "Translation",
    path: "/translation"
  }

]



// -----------------------------------------
// Authenticated User Navigation
// -----------------------------------------

export const USER_NAV_LINKS = [

  {
    label: "Favorites",
    path: "/favorites"
  },

  {
    label: "Notifications",
    path: "/notifications"
  },

  {
    label: "Settings",
    path: "/settings"
  }

]