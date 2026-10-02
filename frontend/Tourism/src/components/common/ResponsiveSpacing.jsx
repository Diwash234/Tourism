import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Spacing component that adapts padding and margin to screen size.
 * - Mobile: Compact spacing
 * - Tablet: Medium spacing
 * - Desktop: Generous spacing
 */
const ResponsiveSpacing = ({
  children,
  padding,
  margin,
  className = '',
  ...props
}) => {
  const { isMobile, isTablet } = useResponsive()

  const getSpacing = (value) => {
    if (!value) return ''
    if (typeof value === 'string') return value
    if (typeof value === 'object') {
      if (isMobile) return value.mobile || ''
      if (isTablet) return value.tablet || ''
      return value.desktop || ''
    }
    return ''
  }

  const paddingClass = getSpacing(padding)
  const marginClass = getSpacing(margin)

  return (
    <div className={`${paddingClass} ${marginClass} ${className}`} {...props}>
      {children}
    </div>
  )
}

export default ResponsiveSpacing
