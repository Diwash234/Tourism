import { useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { FiMenu, FiX, FiUser, FiBell, FiHeart, FiSearch } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import { NAV_LINKS } from "../../utils/constants"
import { resolveSmartSearch } from "../../utils/smartSearch"
import TourismLogo from "../branding/TourismLogo"

const Navbar = () => {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  // NEW: universal search — see utils/smartSearch.js for the honest
  // client-side keyword routing (no fake backend call). Works the same
  // on every page since Navbar renders in both MainLayout and
  // DashboardLayout.
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
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
      <nav className="container-app flex items-center gap-4 h-16">
        <TourismLogo size="md" showTagline={false} />

        {/* Universal smart search — desktop */}
        <form onSubmit={handleSmartSearch} className="hidden md:flex flex-1 max-w-md relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search destinations, hotels, emergency, budget..."
            className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500 focus:border-transparent"
          />
        </form>

        <div className="hidden lg:flex items-center gap-6 shrink-0">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors whitespace-nowrap ${
                  isActive ? "text-himalaya-500" : "text-gray-600 hover:text-dark"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4 shrink-0">
          {isAuthenticated ? (
            <>
              <Link to="/notifications" className="text-gray-600 hover:text-himalaya-500">
                <FiBell size={20} />
              </Link>
              <Link to="/favorites" className="text-gray-600 hover:text-himalaya-500">
                <FiHeart size={20} />
              </Link>
              <Link
                to="/profile"
                className="flex items-center gap-2 border border-gray-200 rounded-full px-3 py-1.5 hover:shadow-card"
              >
                <FiUser />
                <span className="text-sm font-medium">{user?.name || "Profile"}</span>
              </Link>
              <button onClick={handleLogout} className="btn-outline text-sm py-1.5">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-outline text-sm py-1.5">
                Login
              </Link>
              <Link to="/register" className="btn-primary text-sm py-1.5">
                Sign Up
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden text-2xl ml-auto" onClick={() => setOpen(!open)}>
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
              {/* Universal smart search — mobile */}
              <form onSubmit={handleSmartSearch} className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search anything..."
                  className="w-full text-sm rounded-full border border-gray-200 pl-9 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500"
                />
              </form>

              {NAV_LINKS.map((link) => (
                <Link key={link.path} to={link.path} onClick={() => setOpen(false)}>
                  {link.label}
                </Link>
              ))}
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setOpen(false)}>Dashboard</Link>
                  <Link to="/profile" onClick={() => setOpen(false)}>Profile</Link>
                  <Link to="/notifications" onClick={() => setOpen(false)}>Notifications</Link>
                  <button onClick={handleLogout} className="btn-outline">Logout</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)} className="btn-outline text-center">Login</Link>
                  <Link to="/register" onClick={() => setOpen(false)} className="btn-primary text-center">Sign Up</Link>
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