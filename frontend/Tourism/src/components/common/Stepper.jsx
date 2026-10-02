import { FiCheck } from "react-icons/fi"

/**
 * Stepper component for multi-step processes (booking, checkout, forms).
 */
export default function Stepper({ steps, current, onStepClick, orientation = "horizontal", className = "" }) {
  return (
    <div className={`${orientation === "vertical" ? "flex flex-col gap-0" : "flex items-start gap-0"} ${className}`}>
      {steps.map((step, i) => {
        const isCompleted = i < current
        const isActive = i === current
        const isClickable = onStepClick && i <= current

        return (
          <div key={i} className={`flex ${orientation === "vertical" ? "flex-row" : "flex-col items-center"} flex-1`}>
            <div className={`flex items-center ${orientation === "vertical" ? "flex-col" : "w-full"}`}>
              <button
                type="button"
                onClick={() => isClickable && onStepClick(i)}
                disabled={!isClickable}
                className={`flex items-center justify-center h-8 w-8 rounded-full text-xs font-bold transition-all ${
                  isCompleted
                    ? "bg-[var(--ny-green)] text-white"
                    : isActive
                    ? "bg-[var(--ny-green)] text-white ring-4 ring-[var(--ny-soft-green)]"
                    : "bg-gray-200 dark:bg-slate-700 text-gray-500 dark:text-gray-400"
                } ${isClickable ? "cursor-pointer hover:scale-110" : "cursor-default"}`}
                aria-current={isActive ? "step" : undefined}
                aria-label={`Step ${i + 1}: ${step.label}`}
              >
                {isCompleted ? <FiCheck size={14} /> : i + 1}
              </button>
              {i < steps.length - 1 && (
                <div
                  className={`${orientation === "vertical" ? "w-0.5 h-8 mx-auto" : "h-0.5 flex-1 mx-1"} ${
                    isCompleted ? "bg-[var(--ny-green)]" : "bg-gray-200 dark:bg-slate-700"
                  }`}
                />
              )}
            </div>
            <div className={`${orientation === "vertical" ? "ml-3 pb-6" : "mt-2 text-center"}`}>
              <p className={`text-xs font-semibold ${
                isActive ? "text-[var(--ny-green)]" : isCompleted ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"
              }`}>
                {step.label}
              </p>
              {step.description && (
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{step.description}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
