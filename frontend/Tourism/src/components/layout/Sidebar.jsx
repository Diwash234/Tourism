import { NavLink } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiAlertTriangle, FiNavigation, FiSearch, FiGlobe,
  FiMessageCircle, FiBookOpen, FiShield, FiKey,
} from "react-icons/fi"
import useAuth from "../../hooks/useAuth"

const links = [
  { to: "/dashboard", label: "Dashboard", icon: FiHome },
  { to: "/profile", label: "Profile", icon: FiUser },
  { to: "/destinations", label: "Destinations", icon: FiMapPin },
  { to: "/hotels/search", label: "Hotels", icon: FiKey },
  { to: "/budget-estimator", label: "Budget Estimator", icon: FiDollarSign },
  { to: "/risk-alerts", label: "Risk Alerts", icon: FiAlertTriangle },
  { to: "/navigation", label: "Navigation", icon: FiNavigation },
  { to: "/language", label: "District Search", icon: FiSearch },
  { to: "/translation", label: "Translation", icon: FiGlobe },
  { to: "/favorites", label: "Favorites", icon: FiHeart },
  { to: "/history", label: "History", icon: FiClock },
  // NEW: these two routes already existed in App.jsx (/chatbot,
  // /my-bookings) but had no sidebar entry, so they were unreachable
  // from the UI even though they worked if you typed the URL directly.
  { to: "/my-bookings", label: "My Bookings", icon: FiBookOpen },
  { to: "/chatbot", label: "AI Chatbot", icon: FiMessageCircle },
  { to: "/notifications", label: "Notifications", icon: FiBell },
  { to: "/settings", label: "Settings", icon: FiSettings },
]

const Sidebar = () => {
  const { isAdmin } = useAuth()

  return (
    <aside className="hidden lg:block w-64 shrink-0 bg-white rounded-xl2 shadow-card p-4 h-fit sticky top-20">
      <nav className="flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-himalaya-50 text-himalaya-600"
                  : "text-gray-600 hover:bg-gray-50"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}

        {/* NEW: only shown to users whose account role is "admin".
            Route already existed (/admin, guarded by AdminRoute) but had
            no link anywhere, so admins had no way to find their own
            dashboard short of typing the URL. */}
        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors mt-2 border-t border-gray-100 pt-4 ${
                isActive
                  ? "text-nepalred-600"
                  : "text-nepalred-500 hover:bg-nepalred-50"
              }`
            }
          >
            <FiShield size={18} />
            Admin Dashboard
          </NavLink>
        )}
      </nav>
    </aside>
  )
}

export default Sidebar