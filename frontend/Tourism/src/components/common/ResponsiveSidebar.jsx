import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FiChevronDown, FiChevronRight } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Sidebar component that adapts to different screen sizes.
 * - Mobile: Slide-out drawer with overlay
 * - Tablet: Collapsible sidebar
 * - Desktop: Fixed sidebar
 */
const ResponsiveSidebar = ({
  links,
  logo,
  user,
  onLogout,
  isOpen,
  onClose,
  className = '',
}) => {
  const [expandedGroups, setExpandedGroups] = useState({})
  const { isMobile, isTablet } = useResponsive()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  const toggleGroup = (index) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [index]: !prev[index],
    }))
  }

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      {logo && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <Link to="/" onClick={onClose}>
            {logo}
          </Link>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-1">
          {links.map((link, index) => (
            <li key={index}>
              {link.children ? (
                <div>
                  <button
                    onClick={() => toggleGroup(index)}
                    className="w-full flex items-center justify-between p-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                  >
                    <span className="flex items-center gap-3">
                      {link.icon}
                      <span>{link.label}</span>
                    </span>
                    {expandedGroups[index] ? (
                      <FiChevronDown className="w-4 h-4" />
                    ) : (
                      <FiChevronRight className="w-4 h-4" />
                    )}
                  </button>
                  {expandedGroups[index] && (
                    <ul className="ml-4 mt-1 space-y-1">
                      {link.children.map((child, childIndex) => (
                        <li key={childIndex}>
                          <Link
                            to={child.path}
                            onClick={onClose}
                            className={`block p-2 text-sm rounded-lg ${
                              isActive(child.path)
                                ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
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
                  onClick={onClose}
                  className={`flex items-center gap-3 p-3 rounded-lg ${
                    isActive(link.path)
                      ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  {link.icon}
                  <span>{link.label}</span>
                </Link>
              )}
            </li>
          ))}
        </ul>
      </nav>

      {/* User Section */}
      {user && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold">
              {user.first_name?.[0] || user.email?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="text-sm text-red-600 hover:text-red-700"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )

  // Mobile: Drawer
  if (isMobile) {
    return (
      <>
        {isOpen && (
          <div className="fixed inset-0 z-50">
            <div className="fixed inset-0 bg-black/50" onClick={onClose} />
            <div className="fixed top-0 left-0 bottom-0 w-80 max-w-[85vw] bg-white dark:bg-gray-900 shadow-xl">
              {sidebarContent}
            </div>
          </div>
        )}
      </>
    )
  }

  // Tablet/Desktop: Sidebar
  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 z-40 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-300 ${className}`}
    >
      {sidebarContent}
    </aside>
  )
}

export default ResponsiveSidebar
