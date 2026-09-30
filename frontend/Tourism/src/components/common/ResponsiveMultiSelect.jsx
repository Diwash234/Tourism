import { useState } from 'react'
import { FiChevronDown, FiCheck, FiX } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Multi-Select component that adapts to different screen sizes.
 * - Mobile: Native multi-select
 * - Tablet/Desktop: Custom dropdown with checkboxes
 */
const ResponsiveMultiSelect = ({
  value = [],
  onChange,
  options,
  placeholder = 'Select...',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { isMobile } = useResponsive()

  const selectedOptions = options.filter((opt) => value.includes(opt.value))

  const toggleOption = (optionValue) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue))
    } else {
      onChange([...value, optionValue])
    }
  }

  // Mobile: Native multi-select
  if (isMobile) {
    return (
      <div className={className}>
        <select
          multiple
          value={value}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions).map((opt) => opt.value)
            onChange(selected)
          }}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100 min-h-[100px]"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {selectedOptions.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {selectedOptions.map((opt) => (
              <span
                key={opt.value}
                className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 text-xs rounded-full"
              >
                {opt.label}
                <button
                  onClick={() => toggleOption(opt.value)}
                  className="hover:text-emerald-900"
                >
                  <FiX className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Desktop: Custom dropdown
  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100 text-left min-h-[42px]"
      >
        <div className="flex flex-wrap gap-1 flex-1">
          {selectedOptions.length > 0 ? (
            selectedOptions.map((opt) => (
              <span
                key={opt.value}
                className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 text-xs rounded-full"
              >
                {opt.label}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleOption(opt.value)
                  }}
                  className="hover:text-emerald-900"
                >
                  <FiX className="w-3 h-3" />
                </button>
              </span>
            ))
          ) : (
            <span className="text-gray-400">{placeholder}</span>
          )}
        </div>
        <FiChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute z-50 mt-2 w-full bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg max-h-64 overflow-y-auto">
            <div className="py-1">
              {options.map((option) => (
                <button
                  key={option.value}
                  onClick={() => toggleOption(option.value)}
                  className={`w-full flex items-center justify-between px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-800 ${
                    value.includes(option.value)
                      ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                      : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  <span>{option.label}</span>
                  {value.includes(option.value) && <FiCheck className="w-4 h-4" />}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ResponsiveMultiSelect
