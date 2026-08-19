import { useEffect, useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { FiMenu, FiUser, FiBell, FiHeart, FiSearch } from "react-icons/fi"

import useAuth from "../../hooks/useAuth"
import useSidebarState from "../../hooks/useSidebarState"
import { NAV_LINKS } from "../../utils/constants"
import { resolveSmartSearch } from "../../utils/smartSearch"
import TourismLogo from "../branding/TourismLogo"
import LanguageSwitcher from "../common/LanguageSwitcher"
import { useI18n } from "../../i18n"
import configApi from "../../api/configApi"

const Navbar = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [, , toggleSidebar] = useSidebarState()
  const { isAuthenticated, user, logout } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [managedLinks, setManagedLinks] = useState(NAV_LINKS)

  useEffect(() => {
    configApi.getPublicConfig().then(({data}) => {
      const items=(data.navigation||[]).filter(item=>item.location==="navbar"&&!item.parent_id&&String(item.route).startsWith("/"))
      if(items.length)setManagedLinks(items.map(item=>({path:item.route,label:item.label})))
    }).catch(()=>{})
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  const handleSmartSearch = (e) => {
    e.preventDefault()
    const destination = resolveSmartSearch(searchQuery)

    if (destination) {
      navigate(destination)
      setSearchQuery("")
    }
  }

  return (
    <header className="sticky top-0 left-0 right-0 z-[60] bg-white/95 backdrop-blur border-b border-gray-100 w-full min-w-0">
      <nav className="w-full mx-auto px-2 sm:px-3 lg:px-5 flex items-center gap-2 sm:gap-3 h-16">

        {/* Sidebar Toggle */}
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-gray-600 hover:text-primary-600 hover:bg-gray-100 transition-colors shrink-0 flex items-center justify-center"
          aria-label="Toggle sidebar menu"
          title="Toggle sidebar menu"
        >
          <FiMenu size={20} />
        </button>

        <TourismLogo size="md" showTagline={false} />

        {/* Search (visible on all screens; grows to fill space) */}
        <form
          onSubmit={handleSmartSearch}
          className="flex flex-1 max-w-md relative"
        >
          <FiSearch
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            size={16}
          />

          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search destinations, hotels, emergency, budget..."
            className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </form>

        {/* Desktop Navigation */}
        <div className="hidden lg:flex items-center gap-6 shrink-0">
          {managedLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? "text-primary-600"
                    : "text-gray-600 hover:text-dark"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        {/* Desktop User Actions */}
        <div className="hidden md:flex items-center gap-3 shrink-0">
          <LanguageSwitcher compact />
          {isAuthenticated ? (
            <>
              <Link
                to="/notifications"
                className="text-gray-600 hover:text-primary-600"
                aria-label="Notifications"
              >
                <FiBell size={20} />
              </Link>

              <Link
                to="/favorites"
                className="text-gray-600 hover:text-primary-600"
                aria-label="Favorites"
              >
                <FiHeart size={20} />
              </Link>

              <Link
                to="/profile"
                className="flex items-center gap-2 border border-gray-200 rounded-full px-3 py-1.5 hover:shadow-card"
              >
                <FiUser />
                <span className="text-sm font-medium max-w-[120px] truncate">
                  {user?.first_name || user?.name || t("nav.profile")}
                </span>
              </Link>

              <button
                onClick={handleLogout}
                className="btn-outline text-sm py-1.5"
              >
                {t("nav.logout")}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-outline text-sm py-1.5">
                {t("nav.login")}
              </Link>

              <Link to="/register" className="btn-primary text-sm py-1.5">
                {t("nav.signup")}
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}

export default Navbar