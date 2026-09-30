import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Checkbox component that adapts to different screen sizes.
 * - Mobile: Larger touch target
 * - Tablet/Desktop: Standard checkbox
 */
const ResponsiveCheckbox = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  return (
    <label className={`flex items-start ${isMobile ? 'gap-3' : 'gap-2'} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`}>
      <div className="relative flex-shrink-0">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={`${isMobile ? 'w-6 h-6' : 'w-5 h-5'} border-2 rounded flex items-center justify-center transition-colors ${
            checked
              ? 'bg-emerald-600 border-emerald-600'
              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
          }`}
        >
          {checked && (
            <svg className={`${isMobile ? 'w-4 h-4' : 'w-3 h-3'} text-white`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
      </div>
      {(label || description) && (
        <div className="flex-1">
          {label && (
            <span className={`font-medium text-gray-900 dark:text-gray-100 ${isMobile ? 'text-base' : 'text-sm'}`}>
              {label}
            </span>
          )}
          {description && (
            <p className={`text-gray-500 dark:text-gray-400 ${isMobile ? 'text-sm' : 'text-xs'}`}>
              {description}
            </p>
          )}
        </div>
      )}
    </label>
  )
}

export default ResponsiveCheckbox
