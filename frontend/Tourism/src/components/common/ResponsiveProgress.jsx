import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Progress component that adapts to different screen sizes.
 * - Mobile: Compact progress bar
 * - Tablet/Desktop: Full progress bar with label
 */
const ResponsiveProgress = ({
  value,
  max = 100,
  label,
  showValue = true,
  size = 'md',
  variant = 'default',
  className = '',
}) => {
  const { isMobile } = useResponsive()
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }

  const variants = {
    default: 'bg-emerald-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-500',
    danger: 'bg-red-600',
    info: 'bg-blue-600',
  }

  return (
    <div className={className}>
      {(label || showValue) && !isMobile && (
        <div className="flex justify-between mb-1">
          {label && <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
          {showValue && <span className="text-sm text-gray-500">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full ${sizes[size]}`}>
        <div
          className={`${variants[variant]} ${sizes[size]} rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
      {isMobile && showValue && (
        <div className="flex justify-between mt-1">
          {label && <span className="text-xs text-gray-500">{label}</span>}
          <span className="text-xs text-gray-500">{Math.round(percentage)}%</span>
        </div>
      )}
    </div>
  )
}

export default ResponsiveProgress
