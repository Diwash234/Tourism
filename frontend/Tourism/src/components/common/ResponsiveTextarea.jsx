import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Textarea component that adapts to different screen sizes.
 * - Mobile: Larger touch target, full-width
 * - Tablet/Desktop: Standard textarea
 */
const ResponsiveTextarea = ({
  value,
  onChange,
  placeholder,
  label,
  error,
  disabled = false,
  required = false,
  rows = 4,
  className = '',
  ...props
}) => {
  const { isMobile } = useResponsive()

  const textareaClasses = `
    w-full
    ${isMobile ? 'px-4 py-3 text-base' : 'px-4 py-2.5 text-base'}
    border rounded-lg
    focus:ring-2 focus:ring-emerald-500 focus:border-transparent
    transition-colors
    resize-y
    ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 dark:border-gray-600'}
    dark:bg-gray-800 dark:text-gray-100
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
  `

  return (
    <div className={className}>
      {label && (
        <label className={`block font-medium text-gray-700 dark:text-gray-300 ${isMobile ? 'text-base mb-2' : 'text-sm mb-1'}`}>
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        rows={isMobile ? Math.max(rows, 5) : rows}
        className={textareaClasses}
        {...props}
      />
      {error && (
        <p className={`mt-1 text-red-500 ${isMobile ? 'text-sm' : 'text-xs'}`} role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default ResponsiveTextarea
