import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Empty State component for better UX.
 * Adapts layout and content to different screen sizes.
 */
const ResponsiveEmptyState = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  return (
    <div className={`flex flex-col items-center justify-center ${isMobile ? 'py-12 px-4' : 'py-16 px-6'} ${className}`}>
      {icon && (
        <div className={`${isMobile ? 'w-12 h-12' : 'w-16 h-16'} bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4`}>
          {icon}
        </div>
      )}
      <h3 className={`font-semibold text-gray-900 dark:text-gray-100 ${isMobile ? 'text-base' : 'text-lg'} mb-2`}>
        {title}
      </h3>
      {description && (
        <p className={`text-gray-500 dark:text-gray-400 text-center ${isMobile ? 'text-sm' : 'text-base'} mb-6 ${isMobile ? 'max-w-xs' : 'max-w-md'}`}>
          {description}
        </p>
      )}
      {action && (
        <div className={isMobile ? 'w-full' : ''}>
          {action}
        </div>
      )}
    </div>
  )
}

export default ResponsiveEmptyState
