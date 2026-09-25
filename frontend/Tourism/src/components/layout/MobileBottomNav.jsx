import { NavLink } from "react-router-dom"
import { BsCalendar3, BsGeoAlt, BsHeart, BsHouseDoor, BsPerson } from "react-icons/bs"
import useAuth from "../../hooks/useAuth"

const MobileBottomNav = () => {
  const { isAuthenticated } = useAuth()
  const items = [
    { to: isAuthenticated ? "/dashboard" : "/", label: "Home", icon: BsHouseDoor, end: true },
    { to: "/destinations", label: "Explore", icon: BsGeoAlt },
    { to: "/itinerary", label: isAuthenticated ? "My trip" : "Plan", icon: BsCalendar3 },
    { to: isAuthenticated ? "/favorites" : "/packages", label: isAuthenticated ? "Saved" : "Packages", icon: BsHeart },
    { to: isAuthenticated ? "/profile" : "/login", label: "Profile", icon: BsPerson },
  ]

  return (
    <nav className="ny-bottom-nav fixed inset-x-0 bottom-0 z-[45] flex min-w-0 items-center justify-around gap-0.5 border-t border-white/10 bg-[var(--ny-green-deepest)] px-1 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 text-[#C7D9D2] shadow-[0_-4px_18px_rgba(4,42,36,0.14)] backdrop-blur lg:hidden" aria-label="Mobile navigation">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex min-h-12 min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-[var(--ny-radius-sm)] px-1 text-[0.7rem] font-semibold transition ${isActive ? "bg-white/10 text-[#63E6BE]" : "text-[#C7D9D2] hover:text-white"}`}>
          <Icon size={19} aria-hidden="true" />
          <span className="max-w-full truncate">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export default MobileBottomNav
