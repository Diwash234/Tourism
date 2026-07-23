import { useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { FiMenu, FiX, FiUser, FiBell, FiHeart } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import { NAV_LINKS, APP_NAME } from "../../utils/constants"
import Logo from "../common/Logo"

const Navbar = () => {
  const [open, setOpen] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <header className="sticky top-0 z-50 bg-dusk-gradient shadow-card">
      <nav className="container-app flex items-center justify-between h-16">
        <Link to="/" className="flex items-center gap-2 text-2xl font-display font-semibold text-white">
          <Logo size={36} variant="sunrise" />
          {APP_NAME}
        </Link>

        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) =>
                `relative text-sm font-medium py-2 transition-colors ${
                  isActive ? "text-marigold-300" : "text-white/80 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {link.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-underline"
                      className="absolute -bottom-0.5 left-0 right-0 h-0.5 bg-marigold-400 rounded-full"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/notifications" className="text-white/80 hover:text-marigold-300 transition">
                <FiBell size={20} />
              </Link>
              <Link to="/favorites" className="text-white/80 hover:text-marigold-300 transition">
                <FiHeart size={20} />
              </Link>
              <Link
                to="/profile"
                className="flex items-center gap-2 border border-white/25 rounded-full px-3 py-1.5 hover:border-white/50 hover:bg-white/10 transition"
              >
                <FiUser className="text-secondary-300" />
                <span className="text-sm font-medium text-white">{user?.name || "Profile"}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="border border-white/30 text-white hover:bg-white/10 text-sm font-semibold px-4 py-1.5 rounded-xl transition"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="border border-white/30 text-white hover:bg-white/10 text-sm font-semibold px-4 py-1.5 rounded-xl transition"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="bg-marigold-500 hover:bg-marigold-600 text-white text-sm font-semibold px-4 py-1.5 rounded-xl transition"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden text-2xl text-white" onClick={() => setOpen(!open)}>
          {open ? <FiX /> : <FiMenu />}
        </button>
      </nav>

      <div className="lungta-strip" />

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden bg-ink border-t border-white/10 overflow-hidden"
          >
            <div className="flex flex-col p-4 gap-3 text-white/90">
              {NAV_LINKS.map((link) => (
                <Link key={link.path} to={link.path} onClick={() => setOpen(false)} className="hover:text-marigold-300 transition">
                  {link.label}
                </Link>
              ))}
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setOpen(false)} className="hover:text-marigold-300 transition">Dashboard</Link>
                  <Link to="/profile" onClick={() => setOpen(false)} className="hover:text-marigold-300 transition">Profile</Link>
                  <button onClick={handleLogout} className="border border-white/30 text-white text-center py-2 rounded-xl hover:bg-white/10 transition">Logout</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)} className="border border-white/30 text-white text-center py-2 rounded-xl hover:bg-white/10 transition">Login</Link>
                  <Link to="/register" onClick={() => setOpen(false)} className="bg-marigold-500 hover:bg-marigold-600 text-white text-center py-2 rounded-xl transition">Sign Up</Link>
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