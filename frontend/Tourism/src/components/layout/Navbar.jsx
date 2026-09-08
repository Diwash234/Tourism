import { useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { FiMenu, FiX, FiUser, FiBell, FiHeart, FiSearch } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import { useTranslation } from "react-i18next"
import useAuth from "../../hooks/useAuth"
import useSidebarState from "../../hooks/useSidebarState"
import { NAV_LINKS } from "../../utils/constants"
import { resolveSmartSearch } from "../../utils/smartSearch"
import TourismLogo from "../branding/TourismLogo"

const Navbar = () => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [, , toggleSidebar] = useSidebarState()
  const [searchQuery, setSearchQuery] = useState("")
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

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
      setOpen(false)
    }
  }

  return (
    <header className="sticky top-0 left-0 right-0 z-[60] bg-white/95 backdrop-blur border-b border-gray-100 w-full min-w-0">
      <nav className="w-full mx-auto px-2 sm:px-3 lg:px-5 flex items-center gap-2 sm:gap-3 h-16">

        {/* Sidebar Toggle */}
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-gray-600 hover:text-himalaya-600 hover:bg-gray-100 transition-colors shrink-0 flex items-center justify-center"
          aria-label="Toggle sidebar menu"
          title={t("common.toggleSidebar")}
        >
          <FiMenu size={20} />
        </button>

        <TourismLogo size="md" showTagline={false} />

        {/* Desktop Search */}
        <form
          onSubmit={handleSmartSearch}
          className="hidden md:flex flex-1 max-w-md relative"
        >
          <FiSearch
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            size={16}
          />

          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("common.searchPlaceholderDesktop")}
            className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500 focus:border-transparent"
          />
        </form>

        {/* Desktop Navigation */}
        <div className="hidden lg:flex items-center gap-6 shrink-0">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? "text-himalaya-500"
                    : "text-gray-600 hover:text-dark"
                }`
              }
            >
              {link.labelKey ? t(link.labelKey) : link.label}
            </NavLink>
          ))}
        </div>

        {/* Desktop User Actions */}
        <div className="hidden md:flex items-center gap-4 shrink-0">
          {isAuthenticated ? (
            <>
              <Link
                to="/notifications"
                className="text-gray-600 hover:text-himalaya-500"
              >
                <FiBell size={20} />
              </Link>

              <Link
                to="/favorites"
                className="text-gray-600 hover:text-himalaya-500"
              >
                <FiHeart size={20} />
              </Link>

              <Link
                to="/profile"
                className="flex items-center gap-2 border border-gray-200 rounded-full px-3 py-1.5 hover:shadow-card"
              >
                <FiUser />
                <span className="text-sm font-medium">
                  {user?.name || t("common.profileFallback")}
                </span>
              </Link>

              <button
                onClick={handleLogout}
                className="btn-outline text-sm py-1.5"
              >
                {t("common.logout")}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-outline text-sm py-1.5">
                {t("common.login")}
              </Link>

              <Link to="/register" className="btn-primary text-sm py-1.5">
                {t("common.signUp")}
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden text-2xl ml-auto"
          onClick={() => setOpen(!open)}
        >
          {open ? <FiX /> : <FiMenu />}
        </button>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden border-t border-gray-100 overflow-hidden"
          >
            <div className="flex flex-col p-4 gap-3">

              {/* Mobile Search */}
              <form
                onSubmit={handleSmartSearch}
                className="relative"
              >
                <FiSearch
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  size={16}
                />

                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t("common.searchPlaceholderMobile")}
                  className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500"
                />
              </form>

              {NAV_LINKS.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setOpen(false)}
                >
                  {link.labelKey ? t(link.labelKey) : link.label}
                </Link>
              ))}

              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setOpen(false)}>
                    {t("nav.dashboard")}
                  </Link>

                  <Link to="/profile" onClick={() => setOpen(false)}>
                    {t("nav.profile")}
                  </Link>

                  <Link to="/notifications" onClick={() => setOpen(false)}>
                    {t("nav.notifications")}
                  </Link>

                  <button
                    onClick={handleLogout}
                    className="btn-outline"
                  >
                    {t("common.logout")}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="btn-outline text-center"
                  >
                    {t("common.login")}
                  </Link>

                  <Link
                    to="/register"
                    onClick={() => setOpen(false)}
                    className="btn-primary text-center"
                  >
                    {t("common.signUp")}
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

export default Navbar