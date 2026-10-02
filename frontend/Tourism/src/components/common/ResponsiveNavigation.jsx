import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FiMenu, FiX, FiChevronDown } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Navigation component that adapts to different screen sizes.
 * - Mobile: Hamburger menu with slide-out drawer
 * - Tablet: Collapsible sidebar
 * - Desktop: Full horizontal navigation
 */
const ResponsiveNavigation = ({ links, logo, actions }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [openSubmenu, setOpenSubmenu] = useState(null)
  const { isMobile, isTablet } = useResponsive()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  const toggleSubmenu = (index) => {
    setOpenSubmenu(openSubmenu === index ? null : index)
  }

  // Mobile Navigation
  if (isMobile) {
    return (
      <>
        {/* Mobile Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-4 h-16">
            <Link to="/" className="flex items-center gap-2">
              {logo}
            </Link>
            <div className="flex items-center gap-2">
              {actions}
              <button
                onClick={() => setIsOpen(true)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                aria-label="Open menu"
              >
                <FiMenu className="w-6 h-6" />
              </button>
            </div>
          </div>
        </header>

        {/* Mobile Drawer */}
        {isOpen && (
          <div className="fixed inset-0 z-50">
            <div className="fixed inset-0 bg-black/50" onClick={() => setIsOpen(false)} />
            <div className="fixed top-0 right-0 bottom-0 w-80 max-w-[85vw] bg-white dark:bg-gray-900 shadow-xl">
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                <span className="font-semibold">Menu</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-gray-600 dark:text-gray-400"
                  aria-label="Close menu"
                >
                  <FiX className="w-6 h-6" />
                </button>
              </div>
              <nav className="p-4">
                <ul className="space-y-2">
                  {links.map((link, index) => (
                    <li key={index}>
                      {link.children ? (
                        <div>
                          <button
                            onClick={() => toggleSubmenu(index)}
                            className="w-full flex items-center justify-between p-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                          >
                            <span>{link.label}</span>
                            <FiChevronDown
                              className={`w-4 h-4 transition-transform ${
                                openSubmenu === index ? 'rotate-180' : ''
                              }`}
                            />
                          </button>
                          {openSubmenu === index && (
                            <ul className="ml-4 mt-2 space-y-1">
                              {link.children.map((child, childIndex) => (
                                <li key={childIndex}>
                                  <Link
                                    to={child.path}
                                    onClick={() => setIsOpen(false)}
                                    className="block p-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                                  >
                                    {child.label}
                                  </Link>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ) : (
                        <Link
                          to={link.path}
                          onClick={() => setIsOpen(false)}
                          className={`block p-3 rounded-lg ${
                            isActive(link.path)
                              ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                          }`}
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </div>
        )}
      </>
    )
  }

  // Tablet/Desktop Navigation
  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            {logo}
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {links.map((link, index) => (
              <div key={index} className="relative group">
                {link.children ? (
                  <button className="flex items-center gap-1 px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                    {link.label}
                    <FiChevronDown className="w-4 h-4" />
                  </button>
                ) : (
                  <Link
                    to={link.path}
                    className={`px-4 py-2 rounded-lg ${
                      isActive(link.path)
                        ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                        : 'text-gray-700 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    {link.label}
                  </Link>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2">
            {actions}
            {isTablet && (
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 text-gray-600 dark:text-gray-400 md:hidden"
                aria-label="Toggle menu"
              >
                {isOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default ResponsiveNavigation
