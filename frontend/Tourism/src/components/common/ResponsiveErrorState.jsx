import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Error State component for better error handling UX.
 * Adapts layout and content to different screen sizes.
 */
const ResponsiveErrorState = ({
  title = 'Something went wrong',
  description = 'An unexpected error occurred. Please try again.',
  onRetry,
  onGoBack,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  return (
    <div className={`flex flex-col items-center justify-center ${isMobile ? 'py-12 px-4' : 'py-16 px-6'} ${className}`}>
      <div className={`${isMobile ? 'w-12 h-12' : 'w-16 h-16'} bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4`}>
        <svg className={`${isMobile ? 'w-6 h-6' : 'w-8 h-8'} text-red-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className={`font-semibold text-gray-900 dark:text-gray-100 ${isMobile ? 'text-base' : 'text-lg'} mb-2`}>
        {title}
      </h3>
      <p className={`text-gray-500 dark:text-gray-400 text-center ${isMobile ? 'text-sm' : 'text-base'} mb-6 ${isMobile ? 'max-w-xs' : 'max-w-md'}`}>
        {description}
      </p>
      <div className={`flex gap-3 ${isMobile ? 'flex-col w-full' : 'flex-row'}`}>
        {onRetry && (
          <button
            onClick={onRetry}
            className={`px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors ${isMobile ? 'w-full' : ''}`}
          >
            Try Again
          </button>
        )}
        {onGoBack && (
          <button
            onClick={onGoBack}
            className={`px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 ${isMobile ? 'w-full' : ''}`}
          >
            Go Back
          </button>
        )}
      </div>
    </div>
  )
}

export default ResponsiveErrorState
