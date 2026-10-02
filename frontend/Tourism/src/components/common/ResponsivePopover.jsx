import { useState, useRef, useEffect } from 'react'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Popover component that adapts to different screen sizes.
 * - Mobile: Bottom sheet popover
 * - Tablet/Desktop: Inline popover with arrow
 */
const ResponsivePopover = ({
  trigger,
  children,
  position = 'bottom',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const popoverRef = useRef(null)
  const { isMobile } = useResponsive()

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close popover on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const positions = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
    left: 'right-full mr-2',
    right: 'left-full ml-2',
  }

  return (
    <div ref={popoverRef} className={`relative ${className}`}>
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
            className={`absolute z-50 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg ${
              isMobile
                ? 'fixed inset-x-4 bottom-4 top-auto max-h-[70vh] overflow-y-auto'
                : positions[position]
            }`}
          >
            {typeof children === 'function' ? children({ close: () => setIsOpen(false) }) : children}
          </div>
        </>
      )}
    </div>
  )
}

export default ResponsivePopover
