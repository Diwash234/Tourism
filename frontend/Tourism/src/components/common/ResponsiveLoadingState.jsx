import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Loading State component for better loading UX.
 * Adapts layout and content to different screen sizes.
 */
const ResponsiveLoadingState = ({
  message = 'Loading...',
  variant = 'spinner',
  className = '',
}) => {
  const { isMobile } = useResponsive()

  if (variant === 'skeleton') {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 animate-pulse">
          <div className="flex gap-4">
            <div className={`${isMobile ? 'w-16 h-16' : 'w-20 h-20'} bg-gray-200 dark:bg-gray-700 rounded-lg`} />
            <div className="flex-1 space-y-2">
              <div className={`${isMobile ? 'h-4' : 'h-5'} bg-gray-200 dark:bg-gray-700 rounded w-3/4`} />
              <div className={`${isMobile ? 'h-3' : 'h-4'} bg-gray-200 dark:bg-gray-700 rounded w-1/2`} />
              <div className={`${isMobile ? 'h-3' : 'h-4'} bg-gray-200 dark:bg-gray-700 rounded w-2/3`} />
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 animate-pulse">
          <div className="flex gap-4">
            <div className={`${isMobile ? 'w-16 h-16' : 'w-20 h-20'} bg-gray-200 dark:bg-gray-700 rounded-lg`} />
            <div className="flex-1 space-y-2">
              <div className={`${isMobile ? 'h-4' : 'h-5'} bg-gray-200 dark:bg-gray-700 rounded w-3/4`} />
              <div className={`${isMobile ? 'h-3' : 'h-4'} bg-gray-200 dark:bg-gray-700 rounded w-1/2`} />
              <div className={`${isMobile ? 'h-3' : 'h-4'} bg-gray-200 dark:bg-gray-700 rounded w-2/3`} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex flex-col items-center justify-center ${isMobile ? 'py-12' : 'py-16'} ${className}`}>
      <div className={`${isMobile ? 'w-8 h-8' : 'w-12 h-12'} animate-spin rounded-full border-2 border-gray-300 border-t-emerald-600`} />
      <p className={`mt-4 text-gray-500 dark:text-gray-400 ${isMobile ? 'text-sm' : 'text-base'}`}>
        {message}
      </p>
    </div>
  )
}

export default ResponsiveLoadingState
