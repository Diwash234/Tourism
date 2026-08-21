import {
  BsActivity, BsBarChart, BsBell, BsBriefcase, BsChatDots, BsDatabase, BsExclamationTriangle,
  BsFileEarmarkText, BsGear, BsGeoAlt, BsHouseDoor, BsImage, BsLayers, BsPalette, BsPeople,
  BsPinMap, BsSearch, BsShieldLock, BsStar, BsTools, BsTranslate, BsTruck,
} from "react-icons/bs"

export const ADMIN_NAV_GROUPS = [
  { label: "Dashboard", items: [
    ["overview", "Overview & Stats", BsHouseDoor],
    ["reports", "Reports & Analytics", BsBarChart],
    ["data_explorer", "Database & Records", BsDatabase],
    ["research", "AI Destination Discovery", BsSearch],
  ]},
  { label: "People & Operations", items: [
    ["users", "Users", BsPeople, [
      { label: "Pending verification", query: { verified: "false" } },
      { label: "Verified", query: { verified: "true" } },
      { label: "Active", query: { status: "active" } },
      { label: "Inactive", query: { status: "inactive" } },
    ]],
    ["staff_permissions", "Staff", BsShieldLock, [
      { label: "Staff accounts", query: { role: "staff" } },
      { label: "Moderators", query: { role: "content_moderator" } },
      { label: "District managers", query: { role: "district_manager" } },
      { label: "Hotel managers", query: { role: "hotel_manager" } },
    ]],
    ["tracking", "Live Tracking & SOS", BsActivity],
    ["feedback_workspace", "Feedback", BsChatDots],
    ["notification_settings", "Notifications", BsBell],
    ["retention", "Retention & Deletion", BsGear],
  ]},
  { label: "Destinations & Media", items: [
    ["places", "Place Approvals", BsPinMap, [
      { label: "Pending places", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
    ]],
    ["destination_features", "Destination Features", BsStar],
    ["category_translations", "Categories & Translations", BsTranslate],
    ["images", "Image Verification", BsImage, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
      { label: "Rejected", query: { status: "rejected" } },
    ]],
    ["media_library", "Central Media Library", BsLayers, [
      { label: "Pending", query: { status: "pending" } },
      { label: "Approved", query: { status: "approved" } },
      { label: "Rejected", query: { status: "rejected" } },
    ]],
    ["image_pipeline", "Image Acquisition Pipeline", BsTools],
  ]},
  { label: "Content & CMS", items: [
    ["cms", "Pages, Sections & Navigation", BsFileEarmarkText],
    ["branding", "Branding & Theme", BsPalette],
    ["datasets", "Dataset & CSV Manager", BsDatabase],
  ]},
  { label: "Travel Services", items: [
    ["hotel_bookings", "Hotels & Bookings", BsBriefcase],
    ["travel_services", "Restaurants, Transport & Plans", BsTruck],
    ["review_moderation", "Review Moderation", BsStar],
    ["expenses", "Expense ML Data", BsBarChart],
  ]},
  { label: "Safety & Emergency", items: [
    ["emergencies", "Medical SOS", BsExclamationTriangle],
    ["infrastructure", "Community Services, Photos & ML", BsLayers],
    ["risks", "Safety & Hazard ML", BsShieldLock],
    ["safety_management", "Alerts & Safety", BsGeoAlt],
  ]},
]

export const ADMIN_PRIMARY_NAV = ["overview", "reports", "users", "places", "media_library", "safety_management"]
export const adminSectionHref = (section, extra = {}) => {
  const params = new URLSearchParams({ ...(section === "overview" ? {} : { section }), ...extra })
  const query = params.toString()
  return query ? `/admin?${query}` : "/admin"
}
export const findAdminSection = section => ADMIN_NAV_GROUPS.flatMap(group => group.items).find(item => item[0] === section)
