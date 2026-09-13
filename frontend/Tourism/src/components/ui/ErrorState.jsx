import { FiAlertCircle, FiRefreshCw } from "react-icons/fi"
import Button from "./Button"

export default function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this information. Please try again.",
  onRetry,
  className = "",
}) {
  return (
    <div className={`p-8 rounded-3xl bg-slate-50 border border-slate-200 text-center space-y-3 ${className}`}>
      <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
        <FiAlertCircle size={24} />
      </div>
      <div>
        <h4 className="font-extrabold text-slate-900 text-sm">{title}</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={FiRefreshCw} onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  )
}
