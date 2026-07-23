import { NavLink } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiAlertTriangle, FiNavigation, FiGlobe, FiClipboard,
  FiMap, FiPackage, FiGrid, FiBriefcase, FiCompass,
} from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import Logo from "../common/Logo"

const baseLinks = [
  { to: "/dashboard", label: "Dashboard", icon: FiHome },
  { to: "/profile", label: "Profile", icon: FiUser },
  { to: "/personal-details", label: "Personal Details", icon: FiClipboard },
  { to: "/destinations", label: "Destinations", icon: FiMapPin },
  { to: "/recommendation", label: "Recommendations", icon: FiGlobe },
  { to: "/trip-planner", label: "Trip Planner", icon: FiMap },
  { to: "/budget-estimator", label: "Budget Estimator", icon: FiDollarSign },
  { to: "/packages", label: "Packages", icon: FiPackage },
  { to: "/risk-alerts", label: "Risk Alerts", icon: FiAlertTriangle },
  { to: "/navigation", label: "Navigation", icon: FiNavigation },
  { to: "/translation", label: "Translation", icon: FiGlobe },
  { to: "/favorites", label: "Favorites", icon: FiHeart },
  { to: "/history", label: "History", icon: FiClock },
  { to: "/notifications", label: "Notifications", icon: FiBell },
  { to: "/settings", label: "Settings", icon: FiSettings },
]

const localLinks = [
  { to: "/local/dashboard", label: "Local Guide Dashboard", icon: FiHome },
]

const adminLinks = [
  { to: "/admin", label: "Admin Dashboard", icon: FiGrid },
  { to: "/admin/agencies", label: "Agencies & Ratings", icon: FiBriefcase },
]

const Sidebar = () => {
  const { user, isLocal, isAdmin } = useAuth()

  return (
    <aside className="hidden lg:block w-64 shrink-0 rounded-xl2 shadow-card h-fit sticky top-20 overflow-hidden bg-white">
      {/* Vibrant gradient header cap with user snapshot */}
      <div className="bg-sunrise-gradient p-4 flex items-center gap-3">
        <Logo size={34} variant="white" />
        <div className="min-w-0">
          <p className="text-white font-semibold text-sm truncate">{user?.name || "Traveler"}</p>
          <p className="text-white/80 text-xs capitalize truncate">
            {isAdmin ? "Admin account" : isLocal ? "Local guide" : "Traveler account"}
          </p>
        </div>
      </div>

      <nav className="flex flex-col gap-1 p-3">
        {baseLinks.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-sunrise-gradient text-white shadow-sm"
                  : "text-gray-600 hover:bg-primary-50 hover:text-primary-600"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`flex items-center justify-center h-7 w-7 rounded-lg shrink-0 transition-colors ${
                    isActive ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500 group-hover:bg-white group-hover:text-primary-500"
                  }`}
                >
                  <Icon size={15} />
                </span>
                {label}
              </>
            )}
          </NavLink>
        ))}

        {(isLocal || isAdmin) && (
          <>
            <div className="flex items-center gap-2 mt-3 mb-1 px-3">
              <FiCompass className="text-secondary-500" size={12} />
              <span className="text-[11px] font-semibold uppercase tracking-wide text-secondary-600">Local Guide</span>
            </div>
            {localLinks.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-secondary-500 text-white shadow-sm"
                      : "text-gray-600 hover:bg-secondary-50 hover:text-secondary-600"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`flex items-center justify-center h-7 w-7 rounded-lg shrink-0 transition-colors ${
                        isActive ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500 group-hover:bg-white group-hover:text-secondary-500"
                      }`}
                    >
                      <Icon size={15} />
                    </span>
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </>
        )}

        {isAdmin && (
          <>
            <div className="flex items-center gap-2 mt-3 mb-1 px-3">
              <FiCompass className="text-marigold-500" size={12} />
              <span className="text-[11px] font-semibold uppercase tracking-wide text-marigold-600">Admin</span>
            </div>
            {adminLinks.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-marigold-500 text-white shadow-sm"
                      : "text-gray-600 hover:bg-marigold-50 hover:text-marigold-600"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`flex items-center justify-center h-7 w-7 rounded-lg shrink-0 transition-colors ${
                        isActive ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500 group-hover:bg-white group-hover:text-marigold-500"
                      }`}
                    >
                      <Icon size={15} />
                    </span>
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="lungta-strip" />
    </aside>
  )
}

export default Sidebar