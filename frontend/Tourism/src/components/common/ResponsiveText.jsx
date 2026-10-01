import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Text component that adapts font sizes to different screen sizes.
 * - Mobile: Smaller text for better readability
 * - Tablet: Medium text
 - Desktop: Full-size text
 */
const ResponsiveText = ({
  children,
  as: Component = 'p',
  size = 'base',
  className = '',
  ...props
}) => {
  const { isMobile, isTablet: _isTablet } = useResponsive()

  const sizes = {
    xs: isMobile ? 'text-xs' : 'text-sm',
    sm: isMobile ? 'text-sm' : 'text-base',
    base: isMobile ? 'text-base' : 'text-lg',
    lg: isMobile ? 'text-lg' : 'text-xl',
    xl: isMobile ? 'text-xl' : 'text-2xl',
    '2xl': isMobile ? 'text-2xl' : 'text-3xl',
    '3xl': isMobile ? 'text-3xl' : 'text-4xl',
    '4xl': isMobile ? 'text-4xl' : 'text-5xl',
  }

  return (
    <Component className={`${sizes[size]} ${className}`} {...props}>
      {children}
    </Component>
  )
}

export default ResponsiveText
