import { Link, useLocation } from "react-router-dom"
import { FiChevronRight, FiHome } from "react-icons/fi"

const routeLabels = {
  "/": "Home",
  "/destinations": "Destinations",
  "/recommendation": "Recommended",
  "/gallery": "Gallery",
  "/compare": "Compare Places",
  "/explore-map": "Explore by Province",
  "/discover-nepal": "Discover Nepal",
  "/discover": "Find by Activity",
  "/decide": "Which Should I Choose?",
  "/search": "Search",
  "/itinerary": "Trip Planner",
  "/budget-estimator": "Budget Estimator",
  "/before-you-travel": "Before You Travel",
  "/hotels": "Hotels",
  "/hotels/search": "Find Hotels",
  "/emergency": "Emergency Services",
  "/risk-alerts": "Travel Alerts",
  "/navigation": "Navigation",
  "/distances": "Distances & Directions",
  "/language": "Phrasebook",
  "/translation": "Live Translation",
  "/nearby-places": "Nearby Places",
  "/packages": "Travel Packages",
  "/guides": "Guides",
  "/guide-portal": "Guide Portal",
  "/tourism-jobs": "Tourism Jobs",
  "/guide-bookings": "Guide Bookings",
  "/collaborate": "Partner with Us",
  "/chatbot": "Himal AI Assistant",
  "/travel": "Travel Planner",
  "/about": "About Us",
  "/contact": "Contact",
  "/support": "Support",
  "/login": "Login",
  "/register": "Sign Up",
  "/dashboard": "My Dashboard",
  "/personal-details": "Personal Details",
  "/favorites": "Saved Favorites",
  "/notifications": "Notifications",
  "/settings": "Settings",
  "/history": "Visit History",
  "/admin": "Admin Central",
  "/staff": "Staff Operations",
  "/local": "Local Guide Portal",
}

const Breadcrumb = ({ customItems = [] }) => {
  const location = useLocation()
  const pathSegments = location.pathname.split("/").filter(Boolean)

  if (customItems.length > 0) {
    return (
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm overflow-x-auto py-2 px-4 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
        <Link to="/" className="flex items-center gap-1 text-[var(--ny-text-secondary)] hover:text-[var(--ny-green)] transition-colors shrink-0">
          <FiHome size={14} />
          <span className="hidden sm:inline">Home</span>
        </Link>
        {customItems.map((item, idx) => (
          <span key={idx} className="flex items-center gap-1.5 shrink-0">
            <FiChevronRight size={14} className="text-gray-400" />
            {item.to ? (
              <Link to={item.to} className="text-[var(--ny-text-secondary)] hover:text-[var(--ny-green)] transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className="text-[var(--ny-text)] font-medium">{item.label}</span>
            )}
          </span>
        ))}
      </nav>
    )
  }

  if (pathSegments.length === 0) return null

  const items = pathSegments.map((segment, idx) => {
    const path = "/" + pathSegments.slice(0, idx + 1).join("/")
    const label = routeLabels[path] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, " ")
    return { path, label, isLast: idx === pathSegments.length - 1 }
  })

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm overflow-x-auto py-2 px-4 bg-white/50 dark:bg-slate-800/50 rounded-xl backdrop-blur-sm">
      <Link to="/" className="flex items-center gap-1 text-[var(--ny-text-secondary)] hover:text-[var(--ny-green)] transition-colors shrink-0">
        <FiHome size={14} />
        <span className="hidden sm:inline">Home</span>
      </Link>
      {items.map((item, idx) => (
        <span key={idx} className="flex items-center gap-1.5 shrink-0">
          <FiChevronRight size={14} className="text-gray-400" />
          {item.isLast ? (
            <span className="text-[var(--ny-text)] font-medium">{item.label}</span>
          ) : (
            <Link to={item.path} className="text-[var(--ny-text-secondary)] hover:text-[var(--ny-green)] transition-colors">
              {item.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  )
}

export default Breadcrumb
