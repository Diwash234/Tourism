import { motion } from "framer-motion"

export default function SmoothButton({
  children,
  onClick,
  variant = "primary", // primary | secondary | gold | danger | outline
  className = "",
  disabled = false,
  type = "button",
  icon: Icon = null,
  size = "md",
}) {
  const baseVariants = {
    primary: "bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 text-white shadow-md shadow-purple-900/20",
    secondary: "bg-purple-900/70 hover:bg-purple-800 text-purple-100 border border-purple-700/50",
    gold: "bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-gray-950 font-black shadow-md shadow-amber-400/20",
    danger: "bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white shadow-md shadow-rose-600/30",
    outline: "bg-transparent border border-purple-300 text-purple-800 hover:bg-purple-50",
  }

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-lg",
    md: "px-5 py-2.5 text-sm rounded-xl",
    lg: "px-7 py-3.5 text-base font-bold rounded-2xl",
  }

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={!disabled ? { scale: 1.03, y: -1 } : {}}
      whileTap={!disabled ? { scale: 0.97 } : {}}
      transition={{ duration: 0.15 }}
      className={`inline-flex items-center justify-center gap-2 font-semibold transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${baseVariants[variant] || baseVariants.primary} ${sizeClasses[size] || sizeClasses.md} ${className}`}
    >
      {Icon && <Icon size={size === "sm" ? 14 : size === "lg" ? 18 : 16} />}
      {children}
    </motion.button>
  )
}
