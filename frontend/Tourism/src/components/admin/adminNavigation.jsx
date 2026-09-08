import {
  BsActivity, BsBarChart, BsBell, BsBriefcase, BsBuilding, BsChatDots, BsCollection,
  BsDatabase, BsExclamationTriangle, BsFileEarmarkText, BsGear, BsGeoAlt, BsHospital,
  BsGlobe, BsHouseDoor, BsImage, BsLayoutTextWindow, BsLink45Deg, BsMegaphone, BsPalette, BsPeople, BsPinMap, BsSearch, BsShieldLock, BsStar,
  BsSliders, BsTools, BsTranslate, BsTruck, BsSpeedometer2,
} from "react-icons/bs"

// Admin navigation, grouped by WHAT THE WEBSITE MEANS to a non-technical
// admin (Content & CMS / Travel / People / Safety / System) instead of by
// implementation detail. Section ids are unchanged so existing
// /admin?section=... links and bookmarks keep working; no section was
// removed — every previous entry is present exactly once.
export const ADMIN_NAV_GROUPS = [
  { label: "Dashboard", items: [
    ["overview", "Overview & Stats", BsHouseDoor],
  ]},
  { label: "Content & CMS", items: [
    ["cms_overview", "CMS Overview", BsSpeedometer2],
    ["cms", "Pages, Sections & Menus", BsFileEarmarkText],
    ["homepage_manager", "Homepage Manager", BsHouseDoor],
    ["redirects", "Redirects & URLs", BsLink45Deg],
    ["visitor_desk", "Announcements & Notices", BsMegaphone],
    ["featured_destinations", "Featured Content Studio", BsStar],
    ["media_library", "Central Media Library", BsCollection, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
      { label: "Rejected", query: { status: "rejected" } },
    ]],
    ["images", "Image Verification", BsImage, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { section: "media_library", status: "approved" } },
      { label: "Rejected", query: { section: "media_library", status: "rejected" } },
    ]],
    ["image_pipeline", "Image Acquisition Pipeline", BsTools],
    ["branding", "Branding & Theme", BsPalette],
    ["header_navbar", "Header & Navbar", BsLayoutTextWindow],
    ["category_translations", "Categories & Translations", BsTranslate],
    ["content_translations", "Content Translations", BsGlobe],
    ["user_dashboard_control", "User Dashboard Controls", BsSliders],
    ["ai_engine", "Central AI Engine Studio", BsStar],
  ]},
  { label: "Travel Management", items: [
    ["places", "Place Approvals", BsPinMap, [
      { label: "Pending places", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
    ]],
    ["destination_features", "Destination Features", BsStar],
    ["research", "AI Destination Discovery", BsSearch],
    ["hotel_bookings", "Hotels & Bookings", BsBuilding],
    ["marketplace", "Travel Packages & Partners", BsBriefcase],
    ["travel_services", "Restaurants, Transport & Plans", BsTruck],
    ["transport_routes", "Transportation & Routes", BsTruck],
    ["review_moderation", "Review Moderation", BsStar],
    ["expenses", "Expense & Budget Data", BsBarChart],
  ]},
  { label: "People & Operations", items: [
    ["users", "Users", BsPeople, [
      { label: "Pending verification", query: { verified: "false" } },
      { label: "Verified", query: { verified: "true" } },
      { label: "Active", query: { status: "active" } },
      { label: "Inactive", query: { status: "inactive" } },
    ]],
    ["staff_permissions", "Staff", BsShieldLock, [
      { label: "Pending verification", query: { section: "users", role: "staff", verified: "false" } },
      { label: "Verified staff", query: { section: "users", role: "staff", verified: "true" } },
      { label: "Active staff", query: { section: "users", role: "staff", status: "active" } },
      { label: "Staff accounts", query: { section: "users", role: "staff" } },
      { label: "Moderators", query: { section: "users", role: "content_moderator" } },
      { label: "District managers", query: { section: "users", role: "district_manager" } },
      { label: "Hotel managers", query: { section: "users", role: "hotel_manager" } },
    ]],
    ["data_reports", "User Reports & Corrections", BsExclamationTriangle],
    ["feedback_workspace", "Feedback", BsChatDots],
    ["tracking", "Live Tracking & SOS", BsActivity],
    ["notification_settings", "Notifications", BsBell],
  ]},
  { label: "Safety & Emergency", items: [
    ["emergencies", "Medical SOS", BsExclamationTriangle],
    ["emergency_directory", "Emergency directory", BsHospital],
    ["infrastructure", "Community Services, Photos & ML", BsHospital],
    ["risks", "Safety & Hazard ML", BsShieldLock],
    ["safety_management", "Alerts & Safety", BsGeoAlt],
  ]},
  { label: "System & Data", items: [
    ["reports", "Reports & Analytics", BsBarChart],
    ["data_health", "Data Health & Provenance", BsShieldLock],
    ["data_explorer", "Database & Records", BsDatabase],
    ["datasets", "Dataset & CSV Manager", BsDatabase],
    ["retention", "Retention & Deletion", BsGear],
  ]},
]

export const ADMIN_PRIMARY_NAV = ["overview", "cms_overview", "reports", "users", "places", "media_library"]
export const adminSectionHref = (section, extra = {}) => {
  const target = extra.section || section
  const rest = { ...extra }
  delete rest.section
  const params = new URLSearchParams({ ...(target === "overview" ? {} : { section: target }), ...rest })
  const query = params.toString()
  return query ? `/admin?${query}` : "/admin"
}
export const findAdminSection = section => ADMIN_NAV_GROUPS.flatMap(group => group.items).find(item => item[0] === section)
