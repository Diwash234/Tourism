import { motion } from "framer-motion"

export default function LoadingSpinner({ size = "md", text = "Loading..." }) {
  const sizeClasses = {
    sm: "w-5 h-5 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-3">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        className={`${sizeClasses[size] || sizeClasses.md} border-purple-200 border-t-purple-700 rounded-full`}
      />
      {text && <p className="text-xs font-semibold text-purple-800">{text}</p>}
    </div>
  )
}
