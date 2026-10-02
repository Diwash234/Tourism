import { useState } from 'react'
import { FiChevronDown } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Accordion component that adapts to different screen sizes.
 * - Mobile: Full-width accordion with large touch targets
 * - Tablet/Desktop: Standard accordion with hover effects
 */
const ResponsiveAccordion = ({
  items,
  allowMultiple = false,
  defaultOpen = [],
  className = '',
}) => {
  const [openItems, setOpenItems] = useState(defaultOpen)
  const { isMobile } = useResponsive()

  const toggleItem = (index) => {
    if (allowMultiple) {
      setOpenItems((prev) =>
        prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
      )
    } else {
      setOpenItems((prev) => (prev.includes(index) ? [] : [index]))
    }
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {items.map((item, index) => {
        const isOpen = openItems.includes(index)

        return (
          <div
            key={index}
            className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${
              isMobile ? 'p-0' : ''
            }`}
          >
            <button
              onClick={() => toggleItem(index)}
              className={`w-full flex items-center justify-between ${
                isMobile ? 'p-4' : 'p-4'
              } text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors`}
              aria-expanded={isOpen}
              aria-controls={`accordion-panel-${index}`}
            >
              <span className={`font-medium text-gray-900 dark:text-gray-100 ${isMobile ? 'text-base' : 'text-sm'}`}>
                {item.title}
              </span>
              <FiChevronDown
                className={`w-5 h-5 text-gray-400 transition-transform flex-shrink-0 ml-2 ${
                  isOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            <div
              id={`accordion-panel-${index}`}
              className={`overflow-hidden transition-all duration-300 ${
                isOpen ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
              }`}
            >
              <div className={`px-4 pb-4 ${isMobile ? 'text-base' : 'text-sm'} text-gray-600 dark:text-gray-400`}>
                {item.content}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ResponsiveAccordion
