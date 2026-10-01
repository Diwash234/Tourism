import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Skeleton component for loading states.
 * Adapts size and layout to different screen sizes.
 */
const ResponsiveSkeleton = ({
  variant = 'text',
  lines = 1,
  width,
  height,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  const baseClasses = 'animate-pulse bg-gray-200 dark:bg-gray-700 rounded'

  if (variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`${baseClasses} ${isMobile ? 'h-3' : 'h-4'}`}
            style={{ width: width || `${100 - i * 10}%` }}
          />
        ))}
      </div>
    )
  }

  if (variant === 'circle') {
    return (
      <div
        className={`${baseClasses} rounded-full ${className}`}
        style={{ width: width || (isMobile ? '3rem' : '4rem'), height: height || (isMobile ? '3rem' : '4rem') }}
      />
    )
  }

  if (variant === 'rect') {
    return (
      <div
        className={`${baseClasses} ${className}`}
        style={{ width: width || '100%', height: height || (isMobile ? '8rem' : '12rem') }}
      />
    )
  }

  if (variant === 'card') {
    return (
      <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
        <div className={`${baseClasses} ${isMobile ? 'h-32' : 'h-48'} rounded-none`} />
        <div className={`p-${isMobile ? '3' : '4'} space-y-3`}>
          <div className={`${baseClasses} ${isMobile ? 'h-4' : 'h-5'} w-3/4`} />
          <div className={`${baseClasses} ${isMobile ? 'h-3' : 'h-4'} w-1/2`} />
          <div className="flex gap-2">
            <div className={`${baseClasses} ${isMobile ? 'h-6 w-16' : 'h-8 w-20'}`} />
            <div className={`${baseClasses} ${isMobile ? 'h-6 w-16' : 'h-8 w-20'}`} />
          </div>
        </div>
      </div>
    )
  }

  return null
}

export default ResponsiveSkeleton
