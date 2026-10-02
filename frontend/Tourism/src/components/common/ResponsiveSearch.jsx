import { useState } from 'react'
import { FiSearch, FiX } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Search component that adapts to different screen sizes.
 * - Mobile: Full-width search bar
 * - Tablet/Desktop: Inline search with icon
 */
const ResponsiveSearch = ({
  value,
  onChange,
  placeholder = 'Search...',
  onClear,
  className = '',
}) => {
  const [isFocused, setIsFocused] = useState(false)
  const { isMobile } = useResponsive()

  const handleClear = () => {
    onChange('')
    onClear?.()
  }

  return (
    <div className={`relative ${className}`}>
      <FiSearch
        className={`absolute ${isMobile ? 'left-3' : 'left-4'} top-1/2 -translate-y-1/2 text-gray-400 ${
          isMobile ? 'w-4 h-4' : 'w-5 h-5'
        }`}
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={placeholder}
        className={`w-full ${isMobile ? 'pl-9 pr-8 py-2 text-sm' : 'pl-11 pr-10 py-2.5 text-base'} border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
          isFocused
            ? 'border-emerald-500 ring-2 ring-emerald-500/20'
            : 'border-gray-300 dark:border-gray-600'
        } dark:bg-gray-800 dark:text-gray-100`}
      />
      {value && (
        <button
          onClick={handleClear}
          className={`absolute ${isMobile ? 'right-2' : 'right-3'} top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300`}
          aria-label="Clear search"
        >
          <FiX className={`${isMobile ? 'w-4 h-4' : 'w-5 h-5'}`} />
        </button>
      )}
    </div>
  )
}

export default ResponsiveSearch
