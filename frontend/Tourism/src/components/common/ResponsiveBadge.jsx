import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Badge component that adapts to different screen sizes.
 * - Mobile: Smaller badges
 * - Tablet/Desktop: Standard badges
 */
const ResponsiveBadge = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  ...props
}) => {
  const { isMobile } = useResponsive()

  const variants = {
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    primary: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-200',
    secondary: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200',
    success: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200',
    danger: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200',
  }

  const sizes = {
    sm: isMobile ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs',
    md: isMobile ? 'px-2 py-1 text-xs' : 'px-2.5 py-1 text-sm',
    lg: isMobile ? 'px-2.5 py-1 text-sm' : 'px-3 py-1.5 text-base',
  }

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  )
}

export default ResponsiveBadge
