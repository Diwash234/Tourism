import { NavLink } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiAlertTriangle, FiNavigation, FiSearch, FiGlobe,
} from "react-icons/fi"

const links = [
  { to: "/dashboard", label: "Dashboard", icon: FiHome },
  { to: "/profile", label: "Profile", icon: FiUser },
  { to: "/destinations", label: "Destinations", icon: FiMapPin },
  { to: "/budget-estimator", label: "Budget Estimator", icon: FiDollarSign },
  { to: "/risk-alerts", label: "Risk Alerts", icon: FiAlertTriangle },
  { to: "/navigation", label: "Navigation", icon: FiNavigation },
  { to: "/language", label: "District Search", icon: FiSearch },
  { to: "/translation", label: "Translation", icon: FiGlobe },
  { to: "/favorites", label: "Favorites", icon: FiHeart },
  { to: "/history", label: "History", icon: FiClock },
  { to: "/notifications", label: "Notifications", icon: FiBell },
  { to: "/settings", label: "Settings", icon: FiSettings },
]

const Sidebar = () => {
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
                  ? "bg-primary-50 text-primary-600"
                  : "text-gray-600 hover:bg-gray-50"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar