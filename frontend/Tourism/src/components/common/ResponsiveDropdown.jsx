import { useState, useRef, useEffect } from 'react'
import { FiChevronDown } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Dropdown component that adapts to different screen sizes.
 * - Mobile: Full-width dropdown with large touch targets
 * - Tablet/Desktop: Inline dropdown with hover effects
 */
const ResponsiveDropdown = ({
  trigger,
  children,
  align = 'left',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  const { isMobile } = useResponsive()

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close dropdown on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const alignments = {
    left: 'left-0',
    right: 'right-0',
    center: 'left-1/2 -translate-x-1/2',
  }

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <div onClick={() => setIsOpen(!isOpen)}>
        {trigger}
      </div>

      {isOpen && (
        <>
          {/* Backdrop for mobile */}
          {isMobile && (
            <div
              className="fixed inset-0 z-40 bg-black/20"
              onClick={() => setIsOpen(false)}
            />
          )}

          <div
            className={`absolute z-50 mt-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden ${
              isMobile
                ? 'fixed inset-x-4 bottom-4 top-auto max-h-[70vh] overflow-y-auto'
                : `${alignments[align]} min-w-[200px]`
            }`}
          >
            {typeof children === 'function' ? children({ close: () => setIsOpen(false) }) : children}
          </div>
        </>
      )}
    </div>
  )
}

export default ResponsiveDropdown
