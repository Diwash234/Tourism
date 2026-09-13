import { useEffect, useState } from "react"
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom"
import { FiMenu, FiBell, FiSearch, FiChevronDown, FiSun, FiMoon } from "react-icons/fi"

import useAuth from "../../hooks/useAuth"
import useSidebarState from "../../hooks/useSidebarState"
import { NAV_LINKS } from "../../utils/constants"
import { resolveSmartSearch } from "../../utils/smartSearch"
import TourismLogo from "../branding/TourismLogo"
import LanguageSwitcher from "../common/LanguageSwitcher"
import ProfileMenu from "./ProfileMenu"
import { useI18n } from "../../i18n"
import usePublicConfig from "../../hooks/usePublicConfig"
import useTheme from "../../context/ThemeContext"
import { resolveNavbarFeatures } from "../../utils/navbarFeatures"

const NavChildren = ({ items, depth = 0, onNavigate }) => items.map(child => <div key={child.path}><NavLink to={child.path} onClick={onNavigate} className="block px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-primary-600" style={{ paddingLeft: `${12 + depth * 14}px` }}>{child.label}</NavLink>{!!child.children?.length && <NavChildren items={child.children} depth={depth + 1} onNavigate={onNavigate}/>}</div>)

const Navbar = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [sidebarOpen, , toggleSidebar] = useSidebarState()
  const { isAuthenticated, user, isAdmin, isStaff } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [managedLinks, setManagedLinks] = useState(NAV_LINKS)
  const [openMenu, setOpenMenu] = useState(null)
  const location = useLocation()
  const { navigation, settings } = usePublicConfig()
  // Header feature switches (brief §5) — every flag defaults to shown, so a
  // missing setting never hides anything.
  const features = resolveNavbarFeatures(settings?.navbar_features)
  const { isDark, toggleTheme } = useTheme()

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    const role = user?.role || "tourist"
    const allowed = (navigation || []).filter(item => item.location === "navbar" && String(item.route).startsWith("/") && (!item.allowed_roles?.length || item.allowed_roles.includes(role)))
    if (!allowed.length) return setManagedLinks(NAV_LINKS)
    const nodes = new Map(allowed.map(item => [item.id, { path: item.route, label: item.label, children: [] }]))
    const roots = []
    allowed.forEach(item => { const node = nodes.get(item.id); const parent = nodes.get(item.parent_id); if (parent) parent.children.push(node); else roots.push(node) })
    setManagedLinks(roots)
    }, 0)
    return () => clearTimeout(t)
  }, [navigation, user?.role])

  // Close any open dropdown on route change or Escape key
  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => { setOpenMenu(null)
    }, 0)
    return () => clearTimeout(t)
  }, [location.pathname])
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") setOpenMenu(null) }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])
  // Close the open dropdown on any outside click (brief §36: menus must not
  // stay floating over the page).
  useEffect(() => {
    if (openMenu === null) return undefined
    const onDown = (e) => {
      if (!e.target.closest?.("[data-nav-root]")) setOpenMenu(null)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [openMenu])

  const handleSmartSearch = (e) => {
    e.preventDefault()
    const destination = resolveSmartSearch(searchQuery)

    if (destination) {
      navigate(destination)
      setSearchQuery("")
    }
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-[60] bg-white/95 dark:bg-nav-dark/95 backdrop-blur border-b border-nav-tintStrong dark:border-slate-700 shadow-sm w-full min-w-0">
      <nav data-nav-root className="w-full mx-auto px-2 sm:px-3 lg:px-5 flex items-center gap-2 sm:gap-3 h-16 min-w-0">

        {/* Sidebar Toggle */}
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-gray-600 hover:text-primary-600 hover:bg-gray-100 transition-colors shrink-0 flex items-center justify-center min-w-[44px] min-h-[44px]"
          aria-label={sidebarOpen ? "Close sidebar menu" : "Open sidebar menu"}
          aria-expanded={sidebarOpen}
          aria-controls="sidebar-drawer"
          title="Toggle sidebar menu"
        >
          <FiMenu size={20} />
        </button>

        <TourismLogo size="md" showTagline={false} darkText />

        {/* Search (visible on all screens; grows to fill space) */}
        {features.search && <form
          onSubmit={handleSmartSearch}
          className="nav-search-form flex flex-1 min-w-0 max-w-md items-center gap-1.5"
        >
          <div className="relative flex-1 min-w-0">
            <FiSearch
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              size={16}
            />

            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search destinations, map, safety... (Ctrl+K)"
              className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* In normal flow and gated by a container query on the form's own
              width — the badge only exists when the form is genuinely wide
              enough to hold it, so no squeeze (long brand, many nav links)
              can ever push it over neighbouring text. */}
          <button
            type="button"
            onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))}
            className="nav-kbd hidden shrink-0 items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-bold text-gray-500 bg-gray-100 hover:bg-gray-200 border border-gray-200 rounded-md transition-colors"
            title="Open Command Palette (Ctrl+K)"
          >
            <span>Ctrl</span>
            <span>K</span>
          </button>
        </form>}

        {/* Desktop Navigation */}
        <div className="hidden lg:flex items-center gap-4 xl:gap-6 shrink-0">
          {managedLinks.map((link, idx) => (
            <div key={link.id || `${link.path}-${idx}`} className="relative group" onMouseLeave={() => setOpenMenu(null)}>
              <div className="flex items-center gap-0.5">
                <NavLink to={link.path} onClick={() => setOpenMenu(null)} className={({ isActive }) => `text-sm font-medium transition-colors whitespace-nowrap ${isActive ? "text-primary-600" : "text-gray-600 hover:text-dark"}`}>{link.label}</NavLink>
                {!!link.children?.length && (
                  <button
                    type="button"
                    aria-label={`Toggle ${link.label} menu`}
                    aria-expanded={openMenu === idx}
                    onClick={() => setOpenMenu(openMenu === idx ? null : idx)}
                    className={`p-1 rounded transition-colors ${openMenu === idx ? "text-primary-600" : "text-gray-400 hover:text-primary-600"}`}
                  >
                    <FiChevronDown size={14} className={`transition-transform ${openMenu === idx ? "rotate-180" : ""}`} />
                  </button>
                )}
              </div>
              {!!link.children?.length && (
                <div className={`absolute top-full left-0 pt-3 min-w-52 z-50 ${openMenu === idx ? "block" : "hidden"}`}>
                  <div className="bg-white border border-gray-100 shadow-xl rounded-xl p-2">
                    <NavChildren items={link.children} onNavigate={() => setOpenMenu(null)} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Desktop User Actions */}
        <div className="hidden md:flex items-center gap-3 shrink-0 ml-auto">
          {features.language_switcher && <LanguageSwitcher compact />}
          {isAuthenticated ? (
            <>
              {isAdmin && (
                <Link to="/admin" className="text-xs font-black uppercase tracking-wide rounded-lg bg-nav-surface text-white px-3 py-2">
                  Admin
                </Link>
              )}
              {isStaff && !isAdmin && (
                <Link to="/staff" className="text-xs font-black uppercase tracking-wide rounded-lg bg-amber-500 text-amber-950 px-3 py-2">
                  Staff
                </Link>
              )}
              {features.theme_toggle && <button
                type="button"
                onClick={toggleTheme}
                className="text-gray-600 hover:text-primary-600 dark:text-gray-300 dark:hover:text-white"
                aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
                title={isDark ? "Light mode" : "Dark mode"}
              >
                {isDark ? <FiSun size={20} /> : <FiMoon size={20} />}
              </button>}
              {features.notifications && <Link
                to="/notifications"
                className="text-gray-600 hover:text-primary-600 dark:text-gray-300 dark:hover:text-white"
                aria-label="Notifications"
              >
                <FiBell size={20} />
              </Link>}

              {features.profile && <ProfileMenu />}
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