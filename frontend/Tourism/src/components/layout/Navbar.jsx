import { useEffect, useState } from "react"
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom"
import { FiMenu, FiBell, FiSearch, FiChevronDown, FiSun, FiMoon, FiX } from "react-icons/fi"

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

const PUBLIC_NAV_PATHS = new Set([
  "/", "/destinations", "/recommendation", "/gallery", "/compare", "/explore-map", "/discover-nepal",
  "/itinerary", "/budget-estimator", "/before-you-travel", "/hotels/search", "/emergency", "/risk-alerts", "/navigation",
  "/distances", "/language", "/translation", "/nearby-places", "/packages", "/guides", "/guide-portal",
  "/tourism-jobs", "/guide-bookings", "/collaborate", "/chatbot", "/travel", "/about", "/contact", "/support",
])

const NavChildren = ({ items, depth = 0, onNavigate }) => items.map(child => <div key={child.path}><NavLink to={child.path} onClick={onNavigate} className="block px-3 py-2 rounded-lg text-sm text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors" style={{ paddingLeft: `${12 + depth * 14}px` }}>{child.label}</NavLink>{!!child.children?.length && <NavChildren items={child.children} depth={depth + 1} onNavigate={onNavigate}/>}</div>)

const Navbar = () => {
  const [searchQuery, setSearchQuery] = useState("")
  // Below xl the search box is an icon that expands into a full-width bar
  // under the header (the inline box used to be squeezed to a sliver on
  // ~1024px screens, making it unreadable).
  const [searchOpen, setSearchOpen] = useState(false)
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
    const allowed = (navigation || []).filter(item => {
      const route = String(item.route || "")
      const publicRoute = PUBLIC_NAV_PATHS.has(route) || /^\/page\/[^/]+$/.test(route)
      return item.location === "navbar" && route.startsWith("/") && (!item.allowed_roles?.length || item.allowed_roles.includes(role)) && (isAuthenticated || publicRoute)
    })
    if (!allowed.length) return setManagedLinks(NAV_LINKS)
    const nodes = new Map(allowed.map(item => [item.id, { path: item.route, label: item.label, children: [] }]))
    const roots = []
    allowed.forEach(item => { const node = nodes.get(item.id); const parent = nodes.get(item.parent_id); if (parent) parent.children.push(node); else roots.push(node) })
    setManagedLinks(roots)
    }, 0)
    return () => clearTimeout(t)
  }, [navigation, user?.role, isAuthenticated])

  // Close any open dropdown on route change or Escape key
  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => { setOpenMenu(null); setSearchOpen(false)
    }, 0)
    return () => clearTimeout(t)
  }, [location.pathname])
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") { setOpenMenu(null); setSearchOpen(false) } }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])
  // If the viewport crosses the 1400px search breakpoint while the expanding
  // bar is open, close it (the inline box takes over / the icon reappears).
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1400px)")
    const onChange = () => setSearchOpen(false)
    mql.addEventListener?.("change", onChange)
    return () => mql.removeEventListener?.("change", onChange)
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
    <header className="ny-header fixed inset-x-0 top-0 z-[60] min-w-0 w-full border-b border-white/10 text-white shadow-[0_4px_18px_rgba(4,42,36,0.16)] backdrop-blur">
      <nav data-nav-root aria-label="Main navigation" className="relative mx-auto flex h-16 min-w-0 w-full items-center gap-2 px-2 sm:gap-3 sm:px-4 lg:px-6">

        {/* Sidebar Toggle */}
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-[#C7D9D2] hover:text-white hover:bg-white/10 transition-colors shrink-0 flex items-center justify-center min-w-[44px] min-h-[44px]"
          aria-label={sidebarOpen ? "Close sidebar menu" : "Open sidebar menu"}
          aria-expanded={sidebarOpen}
          aria-controls="sidebar-drawer"
          title="Toggle sidebar menu"
        >
          <FiMenu size={20} />
        </button>

        {/* Wordmark hidden below lg — the emblem alone keeps the brand
            visible while freeing room for search + links + actions so
            nothing is ever clipped at tablet/laptop widths. */}
        <TourismLogo size="md" showTagline={false} responsiveText />

        {/* Search: inline box only from 1400px, where it has real room;
            below that it's an icon that opens a full-width bar under the
            header (the old always-inline box squeezed to an unreadable
            sliver at ~1024–1300px widths). */}
        {features.search && <form
          onSubmit={handleSmartSearch}
          className="nav-search-form hidden min-[1400px]:flex flex-1 min-w-0 max-w-md items-center gap-1.5"
        >
          <div className="relative flex-1 min-w-0">
            <FiSearch
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#63E6BE]"
              size={16}
            />

            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search destinations…"
              className="w-full text-sm rounded-full border border-white/20 bg-white/10 text-white placeholder:text-[#AFC5BC] pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>

          {/* In normal flow and gated by a container query on the form's own
              width — the badge only exists when the form is genuinely wide
              enough to hold it, so no squeeze (long brand, many nav links)
              can ever push it over neighbouring text. */}
          <button
            type="button"
            onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))}
            className="nav-kbd hidden shrink-0 items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-bold text-[#BDEBD9] bg-[#063B32] hover:bg-white/10 border border-white/20 rounded-md transition-colors"
            title="Open Command Palette (Ctrl+K)"
          >
            <span>Ctrl</span>
            <span>K</span>
          </button>
        </form>}

        {/* Search toggle (icon) — shown below 1400px, where the inline box
            above is hidden. */}
        {features.search && (
          <button
            type="button"
            onClick={() => setSearchOpen((v) => !v)}
            className="min-[1400px]:hidden p-2 rounded-lg text-[#C7D9D2] hover:text-white hover:bg-white/10 transition-colors shrink-0 flex items-center justify-center min-w-[44px] min-h-[44px]"
            aria-label={searchOpen ? "Close search" : "Open search"}
            aria-expanded={searchOpen}
          >
            <FiSearch size={20} />
          </button>
        )}

        {/* Primary Navigation — inline from laptop (lg) up; the full set of
            five links plus the user actions overflows tablet widths, so at
            md–lg the same tree stays reachable via the sidebar drawer
            (hamburger) and the bottom nav — nothing is ever lost. */}
        <div className="hidden min-[1280px]:flex items-center gap-2 xl:gap-4 shrink-0">
          {managedLinks.map((link, idx) => (
            <div key={link.id || `${link.path}-${idx}`} className="relative group" onMouseLeave={() => setOpenMenu(null)}>
              <div className="flex items-center gap-0.5">
                <NavLink to={link.path} onClick={() => setOpenMenu(null)} className={({ isActive }) => `text-sm font-medium transition-colors whitespace-nowrap rounded-lg px-2.5 py-2 ${isActive ? "bg-white/10 text-white" : "text-[#C7D9D2] hover:bg-white/10 hover:text-white"}`}>{link.label}</NavLink>
                {!!link.children?.length && (
                  <button
                    type="button"
                    aria-label={`Toggle ${link.label} menu`}
                    aria-expanded={openMenu === idx}
                    onClick={() => setOpenMenu(openMenu === idx ? null : idx)}
                    className={`p-1 rounded transition-colors ${openMenu === idx ? "text-white" : "text-[#BDEBD9] hover:text-white"}`}
                  >
                    <FiChevronDown size={14} className={`transition-transform ${openMenu === idx ? "rotate-180" : ""}`} />
                  </button>
                )}
              </div>
              {!!link.children?.length && (
                <div className={`absolute top-full left-0 pt-3 min-w-52 z-50 ${openMenu === idx ? "block" : "hidden"}`}>
                  <div className="bg-[#063B32] border border-white/20 shadow-xl shadow-emerald-950/50 rounded-xl p-2">
                    <NavChildren items={link.children} onNavigate={() => setOpenMenu(null)} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* User actions. Language switcher joins at xl — at 1024–1279 the
            five primary links + auth actions already fill the bar, and the
            switcher stays reachable in the sidebar at every width. */}
        <div className="hidden md:flex items-center gap-3 shrink-0 ml-auto">
          {features.language_switcher && (
            <div className="hidden xl:block">
              <LanguageSwitcher compact />
            </div>
          )}
          {isAuthenticated ? (
            <>
              {isAdmin && (
                <Link to="/admin" className="text-xs font-black uppercase tracking-wide rounded-lg bg-white text-emerald-950 hover:bg-emerald-50 px-3 py-2">
                  Admin
                </Link>
              )}
              {isStaff && !isAdmin && (
                <Link to="/staff" className="text-xs font-black uppercase tracking-wide rounded-lg bg-amber-400 text-amber-950 hover:bg-amber-300 px-3 py-2">
                  Staff
                </Link>
              )}
              {features.theme_toggle && <button
                type="button"
                onClick={toggleTheme}
                className="text-[#BDEBD9] hover:text-white"
                aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
                title={isDark ? "Light mode" : "Dark mode"}
              >
                {isDark ? <FiSun size={20} /> : <FiMoon size={20} />}
              </button>}
              {features.notifications && <Link
                to="/notifications"
                className="text-[#BDEBD9] hover:text-white"
                aria-label="Notifications"
              >
                <FiBell size={20} />
              </Link>}

              {features.profile && <ProfileMenu />}
            </>
          ) : (
            <>
              <Link to="/login" className="inline-flex min-h-11 items-center justify-center gap-2 text-sm font-semibold px-4 py-2 rounded-[var(--ny-radius-sm)] border border-emerald-600 text-white hover:bg-white/10 transition-colors">
                {t("nav.login")}
              </Link>

              <Link to="/register" className="btn-primary min-h-11 text-sm py-2">
                {t("nav.signup")}
              </Link>
            </>
          )}
        </div>

        {/* Mobile user actions (below md) — previously login/register,
            theme, notifications and profile were all absent from the
            navbar on phones. Compact cluster keeps everything reachable.
            (Admin/Staff links stay in the sidebar on small screens.) */}
        <div className="md:hidden flex items-center gap-1 shrink-0 ml-auto">
          {features.theme_toggle && (
            <button
              type="button"
              onClick={toggleTheme}
              className="ny-navbar-secondary-action p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
              aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
            >
              {isDark ? <FiSun size={18} /> : <FiMoon size={18} />}
            </button>
          )}
          {isAuthenticated ? (
            <>
              {features.notifications && (
                <Link to="/notifications" className="p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors" aria-label="Notifications">
                  <FiBell size={18} />
                </Link>
              )}
              {features.profile && <ProfileMenu />}
            </>
          ) : (
            <>
              <Link to="/login" className="text-xs font-bold px-2 py-2 min-h-11 rounded-lg bg-[var(--ny-green)] text-white hover:bg-emerald-500 transition-colors">
                {t("nav.login")}
              </Link>
              <Link to="/register" className="ny-navbar-secondary-action text-xs font-bold px-2 py-2 min-h-11 rounded-lg border border-emerald-600 text-[#C7D9D2] hover:bg-white/10 transition-colors">
                {t("nav.signup")}
              </Link>
            </>
          )}
        </div>

        {/* Expanding search bar (below 1400px). Full-width under the header
            so it never squeezes the other items. */}
        {searchOpen && (
          <div className="min-[1400px]:hidden absolute top-full inset-x-0 bg-[var(--ny-green-deepest)] backdrop-blur border-b border-emerald-800 shadow-lg shadow-emerald-950/40 px-3 py-2.5 z-50">
            <form
              onSubmit={(e) => { setSearchOpen(false); handleSmartSearch(e) }}
              className="relative"
            >
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#63E6BE]" size={16} />
              <input
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search destinations…"
                className="w-full text-sm rounded-full border border-white/20 bg-white/10 text-white placeholder:text-[#AFC5BC] pl-9 pr-10 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setSearchOpen(false)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
                aria-label="Close search"
              >
                <FiX size={16} />
              </button>
            </form>
          </div>
        )}
      </nav>
    </header>
  )
}

export default Navbar