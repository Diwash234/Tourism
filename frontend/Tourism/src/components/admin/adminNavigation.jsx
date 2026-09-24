import {
  BsActivity, BsBarChart, BsBell, BsBriefcase, BsBuilding, BsChatDots, BsCollection,
  BsCookie, BsDatabase, BsExclamationTriangle, BsFileEarmarkText, BsGear, BsGeoAlt, BsHospital,
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
    ["cms_overview", "CMS Dashboard", BsSpeedometer2],
  ]},
  { label: "Content & CMS", items: [
    ["cms_pages", "Website Pages", BsFileEarmarkText, [
      { label: "Home Page", query: { section: "cms_pages", resource: "pages", page: "home" } },
      { label: "About Page", query: { section: "cms_pages", resource: "pages", page: "about" } },
      { label: "Destinations Page", query: { section: "cms_pages", resource: "pages", page: "destinations" } },
      { label: "Trips & Packages", query: { section: "cms_pages", resource: "pages", page: "packages" } },
      { label: "Recommendations", query: { section: "cms_pages", resource: "pages", page: "recommendation" } },
      { label: "Travel Guides", query: { section: "cms_pages", resource: "pages", page: "guides" } },
      { label: "Blog & Articles", query: { section: "cms_pages", resource: "pages", page: "blog" } },
      { label: "FAQs & Support", query: { section: "cms_pages", resource: "pages", page: "faqs" } },
      { label: "Contact Page", query: { section: "cms_pages", resource: "pages", page: "contact" } },
    ]],
    ["cms_sections", "Page Sections", BsLayoutTextWindow, [
      { label: "Hero Sections", query: { section: "cms_sections", resource: "sections", type: "hero" } },
      { label: "Destination Sections", query: { section: "cms_sections", resource: "sections", type: "destinations" } },
      { label: "Recommendation Sections", query: { section: "cms_sections", resource: "sections", type: "recommendations" } },
      { label: "CTA Sections", query: { section: "cms_sections", resource: "sections", type: "cta" } },
      { label: "Testimonials", query: { section: "cms_sections", resource: "sections", type: "testimonials" } },
      { label: "Custom Sections", query: { section: "cms_sections", resource: "sections", type: "custom" } },
    ]],
    ["destinations", "Destinations", BsPinMap, [
      { label: "All Destinations", query: { section: "destinations", status: "approved" } },
      { label: "Pending Approvals", query: { section: "places", status: "pending" } },
      { label: "Featured Studio", query: { section: "featured_destinations" } },
      { label: "AI Discovery", query: { section: "research" } },
    ]],
    ["travel_content", "Travel Content", BsBriefcase, [
      { label: "Activities & Attractions", query: { section: "travel_services" } },
      { label: "Packages & Tours", query: { section: "marketplace" } },
      { label: "Itineraries", query: { section: "travel_services" } },
      { label: "Travel Tips & Articles", query: { section: "cms_pages", resource: "pages", page: "blog" } },
    ]],
    ["media_library", "Media Library", BsCollection, [
      { label: "Pending Photos", query: { section: "images", status: "pending" } },
      { label: "Approved Photos", query: { section: "media_library", status: "approved" } },
      { label: "Acquisition Pipeline", query: { section: "image_pipeline" } },
    ]],
    ["homepage_manager", "Homepage Manager", BsHouseDoor],
    ["seo_metadata", "SEO & Metadata", BsSearch],
    ["global_content", "Global Content", BsGlobe, [
      { label: "Header & Footer", query: { section: "header_navbar" } },
      { label: "Contact Info", query: { section: "cms_pages", resource: "pages", page: "contact" } },
      { label: "Social Links", query: { section: "header_navbar" } },
      { label: "Branding & Theme", query: { section: "branding" } },
    ]],
    ["announcements", "Announcements", BsMegaphone],
    ["translations", "Translations", BsTranslate, [
      { label: "Categories & Translations", query: { section: "category_translations" } },
      { label: "Content Translations", query: { section: "content_translations" } },
    ]],
    ["publishing", "Publishing", BsFileEarmarkText, [
      { label: "Drafts", query: { section: "publishing", status: "draft" } },
      { label: "Under Review", query: { section: "places", status: "pending" } },
      { label: "Published", query: { section: "publishing", status: "published" } },
      { label: "Revision History", query: { section: "data_reports" } },
    ]],
    ["cms", "CMS Section Manager", BsFileEarmarkText],
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
