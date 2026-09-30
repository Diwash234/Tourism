import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Card component that adapts to different screen sizes.
 * - Mobile: Full-width stacked cards
 * - Tablet: 2-column grid
 * - Desktop: 3-4 column grid
 */
const ResponsiveCard = ({
  children,
  className = '',
  hover = true,
  onClick,
  ...props
}) => {
  const { isMobile } = useResponsive()

  return (
    <div
      className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${
        hover ? 'hover:shadow-lg transition-shadow' : ''
      } ${isMobile ? 'p-4' : 'p-6'} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  )
}

export default ResponsiveCard
