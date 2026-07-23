const variants = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  marigold: "btn-marigold",
  outline: "btn-outline",
  ghost: "text-dark hover:bg-gray-100 px-4 py-2 rounded-xl transition",
  danger: "bg-red-500 hover:bg-red-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  info: "bg-blue-500 hover:bg-blue-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  purple: "bg-purple-500 hover:bg-purple-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  amber: "bg-amber-500 hover:bg-amber-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  emerald: "bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  rose: "bg-rose-500 hover:bg-rose-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
  indigo: "bg-indigo-500 hover:bg-indigo-600 text-white font-semibold px-5 py-2.5 rounded-xl transition",
}

const Button = ({ children, variant = "primary", loading = false, className = "", ...props }) => (
  <button
    className={`${variants[variant]} ${className} inline-flex items-center justify-center gap-2`}
    disabled={loading || props.disabled}
    {...props}
  >
    {loading && (
      <span className="h-4 w-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
    )}
    {children}
  </button>
)

export default Button