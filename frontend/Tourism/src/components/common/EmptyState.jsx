import { FiInbox } from "react-icons/fi"

/**
 * One intentional empty state for catalogue, account, gallery and safety
 * surfaces. It is deliberately compact so a missing API record never looks
 * like a broken page.
 */
const EmptyState = ({
  title = "Nothing here yet",
  subtitle = "There is no information to show yet.",
  icon: Icon = FiInbox,
  action,
  secondaryAction,
  className = "",
}) => (
  <section className={`ny-empty ${className}`} role="status">
    <span className="ny-empty-icon" aria-hidden="true"><Icon size={24} /></span>
    <h2>{title}</h2>
    {subtitle && <p>{subtitle}</p>}
    {(action || secondaryAction) && (
      <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
        {action}
        {secondaryAction}
      </div>
    )}
  </section>
)

export default EmptyState
