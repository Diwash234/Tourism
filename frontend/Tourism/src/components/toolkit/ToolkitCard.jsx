import { Link } from "react-router-dom"
import { FiStar, FiClock, FiZap } from "react-icons/fi"
import { TOOLKIT_CATEGORY_BY_ID } from "../../data/travelToolkit"

/**
 * ToolkitCard — one entry in the Travel Toolkit hub.
 *
 * Deliberately restrained: the design system's own note says a different
 * gradient per card made the product feel like several applications, so every
 * card uses the same quiet green icon tile and the category is carried by a
 * small dot plus a screen-reader label instead of seven colour themes.
 *
 * The whole card is the link (big touch target); the star is a separate
 * control inside it and must not trigger navigation.
 */

const CATEGORY_DOT = {
  plan: "bg-emerald-500",
  explore: "bg-sky-500",
  navigate: "bg-indigo-500",
  safety: "bg-rose-500",
  money: "bg-amber-500",
  connect: "bg-violet-500",
  you: "bg-teal-500",
}

const CATEGORY_LABEL = {
  plan: "Plan a trip",
  explore: "Explore places",
  navigate: "Get around",
  safety: "Stay safe",
  money: "Money & stays",
  connect: "Language & help",
  you: "Your trips",
}

export default function ToolkitCard({ tool, favourite = false, onToggleFavourite, onOpen, showCategory = false }) {
  const Icon = tool.icon
  const category = TOOLKIT_CATEGORY_BY_ID[tool.category]
  const dot = CATEGORY_DOT[tool.category] || "bg-[var(--ny-green)]"
  const categoryLabel = CATEGORY_LABEL[tool.category] || tool.category

  const handleFavourite = (event) => {
    // Inside a <a>; stop the navigation from firing.
    event.preventDefault()
    event.stopPropagation()
    onToggleFavourite?.(tool.id)
  }

  return (
    <div className="group relative h-full">
      <Link
        to={tool.path}
        onClick={() => onOpen?.(tool.id)}
        className="card-base flex h-full flex-col gap-3 rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] p-4 no-underline transition duration-200 hover:-translate-y-0.5 hover:border-[var(--ny-green)] hover:shadow-[var(--ny-shadow-elevated)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ny-green)]"
        data-testid={`toolkit-card-${tool.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] text-[var(--ny-green-dark)] transition group-hover:bg-[var(--ny-green)] group-hover:text-white" aria-hidden="true">
            {Icon && <Icon size={20} />}
          </span>
          <button
            type="button"
            onClick={handleFavourite}
            aria-pressed={favourite}
            aria-label={favourite ? `Remove ${tool.label} from favourites` : `Add ${tool.label} to favourites`}
            className={`grid h-9 w-9 shrink-0 place-items-center rounded-full transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ny-green)] ${
              favourite
                ? "bg-[var(--ny-soft-gold)] text-[var(--ny-warm-gold)]"
                : "text-[var(--ny-text-muted)] hover:bg-[var(--ny-soft-gold)] hover:text-[var(--ny-warm-gold)]"
            }`}
          >
            <FiStar size={17} fill={favourite ? "currentColor" : "none"} />
          </button>
        </div>

        <div className="min-w-0">
          <h3 className="m-0 flex items-center gap-2 text-[0.98rem] font-bold leading-snug text-[var(--ny-text)]">
            <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} aria-hidden="true" />
            {tool.label}
          </h3>
          <p className="mt-1.5 text-[0.83rem] leading-5 text-[var(--ny-text-secondary)]">{tool.blurb}</p>
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-1">
          {showCategory && category && (
            <span className="sr-only">{categoryLabel}</span>
          )}
          {tool.live && (
            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--ny-soft-blue)] px-2 py-0.5 text-[0.68rem] font-semibold text-[var(--ny-info)]">
              <FiZap size={10} aria-hidden="true" /> Live data
            </span>
          )}
          {tool.popular && (
            <span className="rounded-full bg-[var(--ny-soft-gold)] px-2 py-0.5 text-[0.68rem] font-semibold text-[var(--ny-warm-gold)]">
              Popular
            </span>
          )}
          {tool.minutes ? (
            <span className="inline-flex items-center gap-1 text-[0.7rem] text-[var(--ny-text-muted)]">
              <FiClock size={11} aria-hidden="true" /> ~{tool.minutes} min
            </span>
          ) : null}
        </div>
      </Link>
    </div>
  )
}
