import { forwardRef } from "react"
import { FiLoader } from "react-icons/fi"

/**
 * The one traveller-facing button primitive. Keep the old `loading` prop for
 * existing callers while exposing the same visual contract as the newer UI
 * button component.
 */
const VARIANTS = {
  primary: "ny-btn-primary",
  secondary: "ny-btn-secondary",
  outline: "ny-btn-secondary",
  ghost: "ny-btn-ghost",
  link: "ny-btn-link",
  accent: "ny-btn-accent",
  danger: "ny-btn-danger",
}

const SIZES = {
  sm: "ny-btn-sm",
  md: "ny-btn-md",
  lg: "ny-btn-lg",
}

const Button = forwardRef(function Button(
  {
    children,
    variant = "primary",
    size = "md",
    loading = false,
    isLoading = false,
    disabled = false,
    className = "",
    type = "button",
    ...props
  },
  ref,
) {
  const busy = loading || isLoading
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`ny-btn ${VARIANTS[variant] || VARIANTS.primary} ${SIZES[size] || SIZES.md} ${className}`}
      {...props}
    >
      {busy && <FiLoader aria-hidden="true" className="animate-spin" size={16} />}
      <span>{children}</span>
    </button>
  )
})

export default Button
