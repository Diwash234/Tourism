import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Container component that adapts padding and max-width to screen size.
 * - Mobile: Full width with small padding
 * - Tablet: Centered with medium padding
 * - Desktop: Centered with max-width and large padding
 */
const ResponsiveContainer = ({
  children,
  className = '',
  size = 'default',
  ...props
}) => {
  const { isMobile, isTablet } = useResponsive()

  const sizes = {
    default: isMobile ? 'px-4' : isTablet ? 'px-6' : 'px-8',
    small: isMobile ? 'px-2' : isTablet ? 'px-4' : 'px-6',
    large: isMobile ? 'px-6' : isTablet ? 'px-8' : 'px-12',
    full: 'px-0',
  }

  const maxWidths = {
    default: 'max-w-7xl',
    small: 'max-w-3xl',
    large: 'max-w-9xl',
    full: 'max-w-full',
  }

  return (
    <div
      className={`mx-auto ${sizes[size]} ${maxWidths[size]} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export default ResponsiveContainer
