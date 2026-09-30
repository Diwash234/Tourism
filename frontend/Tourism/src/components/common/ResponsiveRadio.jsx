import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Radio component that adapts to different screen sizes.
 * - Mobile: Larger touch target
 * - Tablet/Desktop: Standard radio
 */
const ResponsiveRadio = ({
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
          type="radio"
          checked={checked}
          onChange={() => onChange()}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={`${isMobile ? 'w-6 h-6' : 'w-5 h-5'} border-2 rounded-full flex items-center justify-center transition-colors ${
            checked
              ? 'border-emerald-600'
              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
          }`}
        >
          {checked && (
            <div className={`${isMobile ? 'w-3 h-3' : 'w-2.5 h-2.5'} bg-emerald-600 rounded-full`} />
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

export default ResponsiveRadio
