import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Toggle component that adapts to different screen sizes.
 * - Mobile: Larger touch target
 * - Tablet/Desktop: Standard toggle
 */
const ResponsiveToggle = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  return (
    <label className={`flex items-center ${isMobile ? 'gap-3' : 'gap-2'} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`}>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div
          className={`${isMobile ? 'w-12 h-7' : 'w-10 h-6'} rounded-full transition-colors ${
            checked ? 'bg-emerald-600' : 'bg-gray-300 dark:bg-gray-600'
          }`}
        >
          <div
            className={`${isMobile ? 'w-5 h-5' : 'w-4 h-4'} bg-white rounded-full shadow transition-transform absolute top-1 ${
              checked ? (isMobile ? 'translate-x-6' : 'translate-x-5') : 'translate-x-1'
            }`}
          />
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

export default ResponsiveToggle
