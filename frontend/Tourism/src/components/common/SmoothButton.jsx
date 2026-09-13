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
    primary: "bg-[#102A2E] hover:bg-[#1D5146] text-white font-bold shadow-lg shadow-[#102A2E]/20 border border-[#2E6B5A]/30",
    secondary: "bg-[#1D5146] hover:bg-[#2E6B5A] text-white font-bold border border-white/20 shadow-md",
    gold: "bg-[#D99048] hover:bg-amber-600 text-slate-950 font-black shadow-lg shadow-amber-500/20",
    danger: "bg-rose-700 hover:bg-rose-800 text-white font-bold shadow-md shadow-rose-900/20",
    outline: "bg-transparent border border-[#102A2E]/30 text-[#102A2E] hover:bg-[#F7F8F5] font-bold",
  }

  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-xl",
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
