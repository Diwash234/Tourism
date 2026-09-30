import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Input component that adapts to different screen sizes.
 * - Mobile: Larger touch target, full-width
 * - Tablet/Desktop: Standard input
 */
const ResponsiveInput = ({
  type = 'text',
  value,
  onChange,
  placeholder,
  label,
  error,
  disabled = false,
  required = false,
  icon,
  className = '',
  ...props
}) => {
  const { isMobile } = useResponsive()

  const inputClasses = `
    w-full
    ${isMobile ? 'px-4 py-3 text-base' : 'px-4 py-2.5 text-base'}
    border rounded-lg
    focus:ring-2 focus:ring-emerald-500 focus:border-transparent
    transition-colors
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
      <div className="relative">
        {icon && (
          <div className={`absolute ${isMobile ? 'left-4' : 'left-3'} top-1/2 -translate-y-1/2 text-gray-400`}>
            {icon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`${inputClasses} ${icon ? (isMobile ? 'pl-12' : 'pl-10') : ''}`}
          {...props}
        />
      </div>
      {error && (
        <p className={`mt-1 text-red-500 ${isMobile ? 'text-sm' : 'text-xs'}`} role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default ResponsiveInput
