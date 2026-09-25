import { forwardRef } from "react"
import { FiLoader } from "react-icons/fi"

const VARIANTS = {
  primary: "ny-btn-primary",
  secondary: "ny-btn-secondary",
  emerald: "ny-btn-primary",
  amber: "ny-btn-accent",
  saffron: "ny-btn-accent",
  destructive: "ny-btn-danger",
  danger: "ny-btn-danger",
  ghost: "ny-btn-ghost",
  outline: "ny-btn-secondary",
  link: "ny-btn-link",
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
    isLoading = false,
    loading = false,
    disabled = false,
    className = "",
    icon: Icon,
    type = "button",
    ...props
  },
  ref,
) {
  const busy = isLoading || loading
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`ny-btn ${VARIANTS[variant] || VARIANTS.primary} ${SIZES[size] || SIZES.md} ${className}`}
      {...props}
    >
      {busy ? <FiLoader aria-hidden="true" className="animate-spin" size={16} /> : Icon ? <Icon aria-hidden="true" size={16} /> : null}
      <span>{children}</span>
    </button>
  )
})

Button.displayName = "Button"
export default Button
