import {
  BsActivity, BsBarChart, BsBell, BsBriefcase, BsBuilding, BsChatDots, BsCollection,
  BsCookie, BsDatabase, BsExclamationTriangle, BsFileEarmarkText, BsGear, BsGeoAlt, BsHospital,
  BsGlobe, BsHouseDoor, BsImage, BsLayers, BsLayoutTextWindow, BsLink45Deg, BsMegaphone, BsPalette, BsPeople, BsPinMap, BsSearch, BsShieldLock, BsStar,
  BsSliders, BsTools, BsTranslate, BsTruck, BsSpeedometer2,
} from "react-icons/bs"

// Admin navigation, grouped by WHAT THE WEBSITE MEANS to a non-technical
// admin (Content & CMS / Travel / People / Safety / System) instead of by
// implementation detail. Section ids are unchanged so existing
// /admin?section=... links and bookmarks keep working; no section was
// removed — every previous entry is present exactly once.
export const ADMIN_NAV_GROUPS = [
  { label: "OVERVIEW", items: [
    ["overview", "Dashboard", BsHouseDoor],
  ]},
  { label: "WEBSITE", items: [
    ["cms", "Pages & Sections", BsFileEarmarkText],
    ["homepage_manager", "Homepage", BsHouseDoor],
    ["header_navbar", "Global Sections & Navigation", BsLayoutTextWindow],
    ["branding", "Branding & Theme", BsPalette],
    ["redirects", "Redirects & URLs", BsLink45Deg],
    ["visitor_desk", "Announcements & Notices", BsMegaphone],
    ["cookie_consent", "Cookie Consent", BsCookie],
    ["cms_overview", "CMS Overview", BsSpeedometer2],
  ]},
  { label: "CONTENT", items: [
    ["places", "Destinations", BsPinMap, [
      { label: "Pending places", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
    ]],
    ["destination_features", "Featured Destinations", BsStar],
    ["marketplace", "Travel Packages & Partners", BsBriefcase],
    ["review_moderation", "Reviews & Ratings", BsStar],
    ["feedback_workspace", "Feedback & Enquiries", BsChatDots],
    ["content_lifecycle", "Content Lifecycle", BsLayers],
    ["category_translations", "Categories", BsTranslate],
    ["content_translations", "Content Translations", BsGlobe],
  ]},
  { label: "TRAVEL DATA", items: [
    ["hotel_bookings", "Hotels & Lodges", BsBuilding],
    ["travel_services", "Restaurants & Travel Services", BsTruck],
    ["transport_routes", "Routes & Transportation", BsTruck],
    ["expenses", "Budget & Cost Data", BsBarChart],
    ["research", "Destination Research", BsSearch],
    ["guide_verification", "Guide Verification", BsShieldLock],
  ]},
  { label: "MEDIA", items: [
    ["media_library", "Media Library", BsCollection, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
      { label: "Rejected", query: { status: "rejected" } },
    ]],
    ["images", "Image Review", BsImage, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { section: "media_library", status: "approved" } },
      { label: "Rejected", query: { section: "media_library", status: "rejected" } },
    ]],
    ["image_pipeline", "Image Acquisition", BsTools],
  ]},
  { label: "SAFETY & EMERGENCY", items: [
    ["emergency_directory", "Emergency Directory", BsHospital],
    ["emergencies", "Medical SOS", BsExclamationTriangle],
    ["safety_management", "Alerts & Safety Advisories", BsGeoAlt],
    ["risks", "Hazards & Risk Data", BsShieldLock],
    ["infrastructure", "Community Services", BsHospital],
    ["tracking", "Live Tracking & SOS", BsActivity],
  ]},
  { label: "PEOPLE", items: [
    ["users", "Users", BsPeople, [
      { label: "Pending verification", query: { verified: "false" } },
      { label: "Verified", query: { verified: "true" } },
      { label: "Active", query: { status: "active" } },
      { label: "Inactive", query: { status: "inactive" } },
    ]],
    ["staff_permissions", "Staff & Permissions", BsShieldLock],
    ["data_reports", "Reports & Corrections", BsExclamationTriangle],
    ["notification_settings", "Notifications", BsBell],
  ]},
  { label: "SYSTEM", items: [
    ["reports", "Reports & Analytics", BsBarChart],
    ["data_health", "Data Health & Provenance", BsShieldLock],
    ["data_explorer", "Database & Records", BsDatabase],
    ["datasets", "Datasets & CSV", BsDatabase],
    ["routing_provider", "Routing Provider", BsTruck],
    ["retention", "Retention & Deletion", BsGear],
    ["ai_engine", "AI Engine", BsStar],
  ]},
]

export const ADMIN_PRIMARY_NAV = ["overview", "cms_overview", "reports", "users", "places", "media_library"]

// Frontend navigation is capability-aware for usability only. The matching
// backend capability check remains the security boundary.
export const ADMIN_SECTION_CAPABILITIES = {
  overview: "dashboard", cms_overview: "content", cms: "content", homepage_manager: "content",
  redirects: "content", visitor_desk: "content", featured_destinations: "destinations",
  media_library: "images", images: "images", image_pipeline: "images", branding: "settings",
  header_navbar: "content", cookie_consent: "settings", category_translations: "destinations",
  content_translations: "content", user_dashboard_control: "content", content_lifecycle: "destinations", ai_engine: "datasets",
  places: "destinations", destination_features: "destinations", research: "datasets",
  hotel_bookings: "hotels", marketplace: "marketplace", travel_services: ["restaurants", "transportation", "travel_plans"],
  transport_routes: "transportation", review_moderation: "reviews", guide_verification: "marketplace", expenses: "budget",
  users: "users", staff_permissions: "users", data_reports: "feedback", feedback_workspace: "feedback",
  tracking: "safety", notification_settings: "settings", emergencies: "safety",
  emergency_directory: "safety", infrastructure: "safety", risks: "safety", safety_management: "safety",
  reports: "audit", data_health: "dashboard", data_explorer: "dashboard", datasets: "datasets",
  retention: "settings", routing_provider: "settings",
}

export const canAccessAdminSection = (section, can) => {
  const capability = ADMIN_SECTION_CAPABILITIES[section]
  if (!capability) return true
  const modules = Array.isArray(capability) ? capability : [capability]
  return modules.some((module) => can(module, "view"))
}

export const adminSectionHref = (section, extra = {}) => {
  const target = extra.section || section
  const rest = { ...extra }
  delete rest.section
  const params = new URLSearchParams({ ...(target === "overview" ? {} : { section: target }), ...rest })
  const query = params.toString()
  return query ? `/admin?${query}` : "/admin"
}
export const findAdminSection = section => ADMIN_NAV_GROUPS.flatMap(group => group.items).find(item => item[0] === section)
