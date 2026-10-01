import { useEffect, useState } from 'react'

/**
 * Accessibility utilities for better screen reader support
 * and keyboard navigation across all devices.
 */

/**
 * Hook for managing focus.
 */
export const useFocus = () => {
  const [ref, setRef] = useState(null)

  const focus = () => {
    if (ref) {
      ref.focus()
    }
  }

  return [setRef, focus]
}

/**
 * Hook for announcing messages to screen readers.
 */
export const useAnnouncer = () => {
  const [message, setMessage] = useState('')

  const announce = (msg, _priority = 'polite') => {
    setMessage('')
    setTimeout(() => {
      setMessage(msg)
    }, 100)
  }

  return { message, announce }
}

/**
 * Skip link component for keyboard navigation.
 */
export const SkipLink = ({ href = '#main-content', children = 'Skip to main content' }) => (
  <a
    href={href}
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-emerald-600 focus:text-white focus:rounded-lg"
  >
    {children}
  </a>
)

/**
 * ARIA live region for dynamic content.
 */
export const LiveRegion = ({ message, priority = 'polite' }) => (
  <div
    aria-live={priority}
    aria-atomic="true"
    className="sr-only"
  >
    {message}
  </div>
)

/**
 * Focus trap for modals and dialogs.
 */
export const FocusTrap = ({ children, isActive, onEscape }) => {
  const [_focusableElements, _setFocusableElements] = useState([])

  useEffect(() => {
    if (!isActive) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onEscape) {
        onEscape()
        return
      }

      if (e.key !== 'Tab') return

      const focusable = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )

      const firstElement = focusable[0]
      const lastElement = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault()
          firstElement.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isActive, onEscape])

  if (!isActive) return null

  return <>{children}</>
}

/**
 * Visually hidden component for screen readers.
 */
export const VisuallyHidden = ({ children }) => (
  <span className="sr-only">{children}</span>
)

/**
 * Button with proper ARIA attributes.
 */
export const AccessibleButton = ({
  children,
  onClick,
  disabled = false,
  ariaLabel,
  ariaExpanded,
  ariaPressed,
  className = '',
  ...props
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    aria-label={ariaLabel}
    aria-expanded={ariaExpanded}
    aria-pressed={ariaPressed}
    className={className}
    {...props}
  >
    {children}
  </button>
)

/**
 * Link with proper ARIA attributes.
 */
export const AccessibleLink = ({
  children,
  href,
  ariaLabel,
  className = '',
  ...props
}) => (
  <a
    href={href}
    aria-label={ariaLabel}
    className={className}
    {...props}
  >
    {children}
  </a>
)

/**
 * Form field with proper labeling.
 */
export const AccessibleField = ({
  id,
  label,
  error,
  required = false,
  children,
}) => (
  <div className="space-y-1">
    <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {label}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
    {children}
    {error && (
      <p className="text-sm text-red-500" role="alert">
        {error}
      </p>
    )}
  </div>
)

/**
 * Alert component for error messages.
 */
export const Alert = ({ type = 'info', children, className = '' }) => {
  const styles = {
    info: 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-200 dark:border-blue-800',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-200 dark:border-emerald-800',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-200 dark:border-yellow-800',
    error: 'bg-red-50 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-200 dark:border-red-800',
  }

  return (
    <div
      role="alert"
      className={`p-4 rounded-lg border ${styles[type]} ${className}`}
    >
      {children}
    </div>
  )
}

/**
 * Loading spinner with accessibility.
 */
export const AccessibleSpinner = ({ label = 'Loading...' }) => (
  <div role="status" aria-live="polite" className="flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-emerald-600" />
    <span className="sr-only">{label}</span>
  </div>
)

/**
 * Progress bar with accessibility.
 */
export const AccessibleProgress = ({ value, max = 100, label }) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label}
    >
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
