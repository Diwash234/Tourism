import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Divider component that adapts to different screen sizes.
 * - Mobile: Simple line
 * - Tablet/Desktop: Line with optional label
 */
const ResponsiveDivider = ({ label, className = '' }) => {
  const { isMobile } = useResponsive()

  if (isMobile || !label) {
    return <hr className={`border-gray-200 dark:border-gray-700 ${className}`} />
  }

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
    </div>
  )
}

export default ResponsiveDivider
