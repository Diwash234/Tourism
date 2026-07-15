import { useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { FiMenu, FiX, FiUser, FiBell, FiHeart } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import { NAV_LINKS, APP_NAME } from "../../utils/constants"

const Navbar = () => {
  const [open, setOpen] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
      <nav className="container-app flex items-center justify-between h-16">
        <Link to="/" className="text-2xl font-extrabold text-primary-500">
          {APP_NAME}
        </Link>

        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive ? "text-primary-500" : "text-gray-600 hover:text-dark"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/notifications" className="text-gray-600 hover:text-primary-500">
                <FiBell size={20} />
              </Link>
              <Link to="/favorites" className="text-gray-600 hover:text-primary-500">
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

        <button className="md:hidden text-2xl" onClick={() => setOpen(!open)}>
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
              {NAV_LINKS.map((link) => (
                <Link key={link.path} to={link.path} onClick={() => setOpen(false)}>
                  {link.label}
                </Link>
              ))}
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setOpen(false)}>Dashboard</Link>
                  <Link to="/profile" onClick={() => setOpen(false)}>Profile</Link>
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