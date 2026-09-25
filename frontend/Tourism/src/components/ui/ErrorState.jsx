import { FiAlertCircle, FiRefreshCw } from "react-icons/fi"
import Button from "./Button"

export default function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this information right now.",
  onRetry,
  className = "",
}) {
  return (
    <section className={`ny-empty ${className}`} role="alert">
      <span className="ny-empty-icon" aria-hidden="true" style={{ background: "var(--ny-soft-red)", color: "var(--ny-danger)" }}>
        <FiAlertCircle size={24} />
      </span>
      <h2>{title}</h2>
      <p>{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={FiRefreshCw} onClick={onRetry}>
          Try again
        </Button>
      )}
    </section>
  )
}
