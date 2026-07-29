import { FiMapPin, FiBell, FiCalendar, FiAlertTriangle, FiCheckCircle } from "react-icons/fi"

const TYPE_STYLE = {
  itinerary: { icon: FiMapPin, dot: "bg-himalaya-500", text: "text-himalaya-500" },
  reminder: { icon: FiCalendar, dot: "bg-saffron-500", text: "text-saffron-600" },
  alert: { icon: FiAlertTriangle, dot: "bg-nepalred-500", text: "text-nepalred-500" },
  notification: { icon: FiBell, dot: "bg-forest-500", text: "text-forest-600" },
  done: { icon: FiCheckCircle, dot: "bg-gray-300", text: "text-gray-400" },
}

/**
 * TravelTimeline
 * Shared vertical timeline used for itineraries, booking reminders,
 * and notification feeds.
 *
 * items: [{ id, type: "itinerary"|"reminder"|"alert"|"notification"|"done",
 *            title, description, time }]
 * onItemClick: optional (item) => void — if provided, each row becomes
 * clickable (e.g. Notifications.jsx uses this to mark-as-read).
 */
const TravelTimeline = ({ items = [], onItemClick }) => {
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">Nothing to show yet.</p>
  }

  return (
    <ol className="relative border-l border-gray-100 ml-3">
      {items.map((item, idx) => {
        const style = TYPE_STYLE[item.type] || TYPE_STYLE.notification
        const Icon = style.icon
        const clickable = typeof onItemClick === "function"
        const Wrapper = clickable ? "button" : "div"

        return (
          <li key={item.id ?? idx} className="mb-6 ml-6 last:mb-0">
            <span
              className={`absolute flex items-center justify-center w-6 h-6 rounded-full -left-3 ring-4 ring-white ${style.dot}`}
            >
              <Icon size={12} className="text-white" />
            </span>

            <Wrapper
              onClick={clickable ? () => onItemClick(item) : undefined}
              className={`card-base p-4 w-full text-left ${clickable ? "cursor-pointer" : ""} ${item.dimmed ? "opacity-60" : ""}`}
            >
              <div className="flex items-center justify-between gap-3">
                <h4 className="font-semibold text-dark text-sm">{item.title}</h4>
                {item.time && <time className="text-xs text-gray-400 shrink-0">{item.time}</time>}
              </div>
              {item.description && (
                <p className="text-sm text-gray-500 mt-1">{item.description}</p>
              )}
            </Wrapper>
          </li>
        )
      })}
    </ol>
  )
}

export default TravelTimeline