import {
  BsActivity, BsBarChart, BsBell, BsBriefcase, BsBuilding, BsChatDots, BsCollection,
  BsCookie, BsDatabase, BsExclamationTriangle, BsFileEarmarkText, BsGear, BsGeoAlt, BsHospital,
  BsGlobe, BsHouseDoor, BsImage, BsLayoutTextWindow, BsLink45Deg, BsMegaphone, BsPalette, BsPeople, BsPinMap, BsSearch, BsShieldLock, BsStar,
  BsSliders, BsTools, BsTranslate, BsTruck, BsSpeedometer2,
} from "react-icons/bs"

// Admin Control Center 10-Group Hierarchy
export const ADMIN_NAV_GROUPS = [
  { label: "1. Dashboard", items: [
    ["overview", "Overview & Stats", BsHouseDoor],
    ["cms_overview", "CMS Overview", BsSpeedometer2],
  ]},
  { label: "2. CONTENT", items: [
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
    ["header_navbar", "Header & Navigation", BsGlobe],
    ["category_translations", "Categories & Translations", BsTranslate],
    ["announcements", "Announcements", BsMegaphone],
    ["visitor_desk", "Visitor Notices & Featured", BsStar],
    ["cms", "CMS Section Manager", BsFileEarmarkText],
  ]},
  { label: "3. APPEARANCE", items: [
    ["branding", "Branding & Theme", BsPalette],
    ["homepage_manager", "Homepage Studio", BsHouseDoor],
    ["user_dashboard_control", "User Dashboard Controls", BsSliders],
    ["cookie_consent", "Cookie Consent", BsCookie],
  ]},
  { label: "4. MEDIA", items: [
    ["images", "Pending Image Approvals", BsImage],
    ["media_library", "Central Media Library", BsCollection],
    ["image_pipeline", "Multi-Source Acquisition", BsSearch],
  ]},
  { label: "5. TOURISM DATA", items: [
    ["destinations", "All Destinations", BsPinMap, [
      { label: "Approved Destinations", query: { section: "destinations", status: "approved" } },
      { label: "Pending Approvals", query: { section: "places", status: "pending" } },
      { label: "Featured Studio", query: { section: "featured_destinations" } },
    ]],
    ["places", "Place Approvals", BsPinMap],
    ["destination_features", "Destination Features", BsStar],
    ["hotel_bookings", "Hotels & Stays", BsBuilding],
    ["travel_services", "Restaurants & Services", BsTruck],
    ["transport_routes", "Transportation & Routes", BsTruck],
    ["marketplace", "Travel Packages & Partners", BsBriefcase],
  ]},
  { label: "6. BOOKINGS & MARKETPLACE", items: [
    ["hotel_bookings", "Hotel Bookings", BsBuilding],
    ["marketplace", "Partners & Marketplace", BsBriefcase],
    ["review_moderation", "Review Moderation", BsStar],
    ["guide_verification", "Guide Verification", BsShieldLock],
  ]},
  { label: "7. PEOPLE", items: [
    ["users", "Users & Sub-Admins", BsPeople, [
      { label: "Pending Verification", query: { section: "users", verified: "false" } },
      { label: "Verified Users", query: { section: "users", verified: "true" } },
      { label: "Active Users", query: { section: "users", status: "active" } },
    ]],
    ["staff_permissions", "Staff & Permissions", BsShieldLock],
  ]},
  { label: "8. SAFETY", items: [
    ["emergencies", "Medical SOS", BsExclamationTriangle],
    ["emergency_directory", "Emergency Directory", BsHospital],
    ["infrastructure", "Community Services & ML", BsHospital],
    ["risks", "Safety & Hazard ML", BsShieldLock],
    ["safety_management", "Alerts & Safety", BsGeoAlt],
    ["tracking", "Live Tracking & SOS", BsActivity],
  ]},
  { label: "9. COMMUNICATION", items: [
    ["feedback_workspace", "Feedback Workspace", BsChatDots],
    ["data_reports", "User Reports & Corrections", BsExclamationTriangle],
    ["notification_settings", "Notifications", BsBell],
  ]},
  { label: "10. SYSTEM", items: [
    ["reports", "Reports & Analytics", BsBarChart],
    ["data_health", "Data Health & Provenance", BsShieldLock],
    ["data_explorer", "Database & Records", BsDatabase],
    ["datasets", "Dataset & CSV Manager", BsDatabase],
    ["research", "AI Destination Discovery", BsSearch],
    ["ai_engine", "Central AI Engine Studio", BsTools],
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
