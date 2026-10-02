import { Link } from 'react-router-dom'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Footer component that adapts to different screen sizes.
 * - Mobile: Stacked columns
 * - Tablet: 2-column grid
 * - Desktop: 4-column grid
 */
const ResponsiveFooter = ({ columns, socialLinks, copyright }) => {
  const { isMobile, isTablet } = useResponsive()

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Main Footer Content */}
        <div
          className={`grid gap-8 ${
            isMobile ? 'grid-cols-1' : isTablet ? 'grid-cols-2' : 'grid-cols-4'
          }`}
        >
          {columns.map((column, index) => (
            <div key={index}>
              <h3 className="text-white font-semibold mb-4">{column.title}</h3>
              <ul className="space-y-2">
                {column.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <Link
                      to={link.path}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Social Links */}
        {socialLinks && socialLinks.length > 0 && (
          <div className="flex justify-center gap-4 mt-8 pt-8 border-t border-gray-800">
            {socialLinks.map((social, index) => (
              <a
                key={index}
                href={social.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 hover:bg-emerald-600 hover:text-white transition-colors"
                aria-label={social.label}
              >
                {social.icon}
              </a>
            ))}
          </div>
        )}

        {/* Copyright */}
        {copyright && (
          <div className="text-center text-gray-500 text-sm mt-8 pt-8 border-t border-gray-800">
            {copyright}
          </div>
        )}
      </div>
    </footer>
  )
}

export default ResponsiveFooter
