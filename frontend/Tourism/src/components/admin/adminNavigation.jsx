import { FiActivity, FiAlertTriangle, FiBell, FiBriefcase, FiDatabase, FiDollarSign, FiFileText, FiGlobe, FiHome, FiImage, FiLayers, FiMapPin, FiMessageSquare, FiPieChart, FiSearch, FiSettings, FiShield, FiStar, FiTool, FiTruck, FiUsers } from "react-icons/fi"

export const ADMIN_NAV_GROUPS = [
  { label: "Dashboard", items: [
    ["overview", "Overview & Stats", FiHome],
    ["reports", "Reports & Analytics", FiPieChart],
    ["data_explorer", "Database & Records", FiDatabase],
    ["research", "AI Destination Discovery", FiSearch],
  ]},
  { label: "People & Operations", items: [
    ["users", "Users & Sub-admins", FiUsers],
    ["staff_permissions", "Staff Permissions", FiShield],
    ["tracking", "Live Tracking & SOS", FiActivity],
    ["feedback_workspace", "Feedback", FiMessageSquare],
    ["notification_settings", "Notifications", FiBell],
    ["retention", "Retention & Deletion", FiSettings],
  ]},
  { label: "Destinations & Media", items: [
    ["places", "Place Approvals", FiMapPin],
    ["destination_features", "Destination Features", FiStar],
    ["category_translations", "Categories & Translations", FiGlobe],
    ["images", "Image Verification", FiImage],
    ["media_library", "Central Media Library", FiLayers],
    ["image_pipeline", "Image Acquisition Pipeline", FiTool],
  ]},
  { label: "Content & CMS", items: [
    ["cms", "Pages, Sections & Navigation", FiFileText],
    ["branding", "Branding & Theme", FiSettings],
    ["datasets", "Dataset & CSV Manager", FiDatabase],
  ]},
  { label: "Travel Services", items: [
    ["hotel_bookings", "Hotels & Bookings", FiBriefcase],
    ["travel_services", "Restaurants, Transport & Plans", FiTruck],
    ["review_moderation", "Review Moderation", FiStar],
    ["expenses", "Expense ML Data", FiDollarSign],
  ]},
  { label: "Safety & Emergency", items: [
    ["emergencies", "Medical SOS", FiAlertTriangle],
    ["infrastructure", "Community Services & ML", FiLayers],
    ["risks", "Safety & Hazard ML", FiShield],
    ["safety_management", "Alerts & Safety", FiAlertTriangle],
  ]},
]

export const ADMIN_PRIMARY_NAV = ["overview", "reports", "users", "places", "media_library", "safety_management"]
export const adminSectionHref = section => section === "overview" ? "/admin" : `/admin?section=${section}`
export const findAdminSection = section => ADMIN_NAV_GROUPS.flatMap(group => group.items).find(item => item[0] === section)
