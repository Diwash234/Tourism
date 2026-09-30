/**
 * Loading states and skeleton components for better UX.
 * Provides consistent loading indicators across all devices.
 */

// Spinner
export const Spinner = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  }

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-emerald-600 ${sizes[size]} ${className}`} />
  )
}

// Page Loader
export const PageLoader = ({ message = 'Loading...' }) => (
  <div className="flex flex-col items-center justify-center min-h-[320px] p-8">
    <Spinner size="lg" />
    <p className="mt-4 text-gray-500 dark:text-gray-400">{message}</p>
  </div>
)

// Card Skeleton
export const CardSkeleton = () => (
  <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
    <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4" />
    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4" />
    <div className="space-y-2">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded" />
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
    </div>
  </div>
)

// List Skeleton
export const ListSkeleton = ({ count = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 animate-pulse">
        <div className="flex gap-4">
          <div className="w-20 h-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          <div className="flex-1 space-y-2">
            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          </div>
        </div>
      </div>
    ))}
  </div>
)

// Table Skeleton
export const TableSkeleton = ({ rows = 5, cols = 4 }) => (
  <div className="overflow-x-auto">
    <table className="min-w-full">
      <thead>
        <tr>
          {Array.from({ length: cols }).map((_, i) => (
            <th key={i} className="px-4 py-3">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, i) => (
          <tr key={i}>
            {Array.from({ length: cols }).map((_, j) => (
              <td key={j} className="px-4 py-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 animate-pulse" />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)

// Button Loader
export const ButtonLoader = ({ children, loading, className = '' }) => (
  <button
    disabled={loading}
    className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
  >
    {loading && <Spinner size="sm" />}
    {children}
  </button>
)

// Error State
export const ErrorState = ({ message = 'Something went wrong', onRetry }) => (
  <div className="flex flex-col items-center justify-center min-h-[320px] p-8 text-center">
    <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4">
      <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    </div>
    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Error</h3>
    <p className="text-gray-500 dark:text-gray-400 mb-4">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
      >
        Try Again
      </button>
    )}
  </div>
)

// Empty State
export const EmptyState = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center min-h-[320px] p-8 text-center">
    {icon && (
      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
        {icon}
      </div>
    )}
    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
    {description && <p className="text-gray-500 dark:text-gray-400 mb-4">{description}</p>}
    {action && <div>{action}</div>}
  </div>
)

// Inline Loader
export const InlineLoader = ({ message = 'Loading...' }) => (
  <div className="flex items-center justify-center gap-2 py-4">
    <Spinner size="sm" />
    <span className="text-sm text-gray-500">{message}</span>
  </div>
)

// Progress Bar
export const ProgressBar = ({ value, max = 100, className = '' }) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 ${className}`}>
      <div
        className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}
