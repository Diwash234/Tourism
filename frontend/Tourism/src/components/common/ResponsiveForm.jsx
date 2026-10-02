import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Form components that adapt to different screen sizes.
 * Provides optimal form experience across all devices.
 */

// Form Container
export const ResponsiveForm = ({ children, onSubmit, className = '' }) => {
  const { isMobile } = useResponsive()

  return (
    <form
      onSubmit={onSubmit}
      className={`space-y-${isMobile ? '4' : '6'} ${className}`}
    >
      {children}
    </form>
  )
}

// Form Row
export const FormRow = ({ children, cols = 1, className = '' }) => {
  const { isMobile } = useResponsive()

  if (isMobile || cols === 1) {
    return <div className={`space-y-4 ${className}`}>{children}</div>
  }

  return (
    <div className={`grid grid-cols-${cols} gap-4 ${className}`}>
      {children}
    </div>
  )
}

// Form Group
export const FormGroup = ({ label, error, required, children, className = '' }) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {children}
      {error && (
        <p className="mt-1 text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

// Input
export const FormInput = ({ error, className = '', ...props }) => {
  const { isMobile } = useResponsive()

  return (
    <input
      className={`w-full px-${isMobile ? '3' : '4'} py-${isMobile ? '2' : '2.5'} border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
        error
          ? 'border-red-500 focus:ring-red-500'
          : 'border-gray-300 dark:border-gray-600'
      } dark:bg-gray-800 dark:text-gray-100 ${className}`}
      {...props}
    />
  )
}

// Select
export const FormSelect = ({ error, children, className = '', ...props }) => {
  const { isMobile } = useResponsive()

  return (
    <select
      className={`w-full px-${isMobile ? '3' : '4'} py-${isMobile ? '2' : '2.5'} border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
        error
          ? 'border-red-500 focus:ring-red-500'
          : 'border-gray-300 dark:border-gray-600'
      } dark:bg-gray-800 dark:text-gray-100 ${className}`}
      {...props}
    >
      {children}
    </select>
  )
}

// Textarea
export const FormTextarea = ({ error, className = '', ...props }) => {
  const { isMobile } = useResponsive()

  return (
    <textarea
      className={`w-full px-${isMobile ? '3' : '4'} py-${isMobile ? '2' : '2.5'} border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
        error
          ? 'border-red-500 focus:ring-red-500'
          : 'border-gray-300 dark:border-gray-600'
      } dark:bg-gray-800 dark:text-gray-100 ${className}`}
      {...props}
    />
  )
}

// Checkbox
export const FormCheckbox = ({ label, error, className = '', ...props }) => {
  return (
    <div className={className}>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
          {...props}
        />
        <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
      </label>
      {error && (
        <p className="mt-1 text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

// Radio Group
export const FormRadioGroup = ({ label, options, error, className = '', ...props }) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
      )}
      <div className="space-y-2">
        {options.map((option) => (
          <label key={option.value} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value={option.value}
              className="w-4 h-4 text-emerald-600 border-gray-300 focus:ring-emerald-500"
              {...props}
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">{option.label}</span>
          </label>
        ))}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

// Submit Button
export const FormSubmit = ({ children, loading, className = '', ...props }) => {
  const { isMobile } = useResponsive()

  return (
    <button
      type="submit"
      disabled={loading}
      className={`w-full bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
        isMobile ? 'py-2.5 text-sm' : 'py-3 text-base'
      } ${className}`}
      {...props}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Processing...
        </span>
      ) : (
        children
      )}
    </button>
  )
}

export default ResponsiveForm
