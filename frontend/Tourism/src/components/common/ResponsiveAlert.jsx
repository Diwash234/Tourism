import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Alert component that adapts to different screen sizes.
 * - Mobile: Full-width alerts with stacked content
 * - Tablet/Desktop: Inline alerts with icon and action
 */
const ResponsiveAlert = ({
  type = 'info',
  title,
  children,
  action,
  onClose,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  const types = {
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-800 dark:text-blue-200',
      icon: 'text-blue-500',
    },
    success: {
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
      border: 'border-emerald-200 dark:border-emerald-800',
      text: 'text-emerald-800 dark:text-emerald-200',
      icon: 'text-emerald-500',
    },
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-800 dark:text-yellow-200',
      icon: 'text-yellow-500',
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-800 dark:text-red-200',
      icon: 'text-red-500',
    },
  }

  const style = types[type] || types.info

  return (
    <div
      className={`p-4 rounded-lg border ${style.bg} ${style.border} ${className}`}
      role="alert"
    >
      <div className={`flex ${isMobile ? 'flex-col' : 'items-start gap-3'}`}>
        <div className={`flex-1 ${style.text}`}>
          {title && <p className="font-medium mb-1">{title}</p>}
          <div className={isMobile ? 'text-sm' : ''}>{children}</div>
        </div>
        {action && (
          <div className={isMobile ? 'mt-3' : 'flex-shrink-0'}>
            {action}
          </div>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className={`${isMobile ? 'absolute top-2 right-2' : 'flex-shrink-0'} ${style.text} hover:opacity-70`}
            aria-label="Close alert"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}

export default ResponsiveAlert
