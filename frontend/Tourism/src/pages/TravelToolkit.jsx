import { useEffect, useMemo, useRef, useState } from "react"
import { FiSearch, FiX, FiStar, FiClock, FiZap, FiGrid, FiChevronRight } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import EmptyState from "../components/common/EmptyState"
import ToolkitCard from "../components/toolkit/ToolkitCard"
import useSeo from "../hooks/useSeo"
import useDebounce from "../hooks/useDebounce"
import useToolkitState from "../hooks/useToolkitState"
import useAuth from "../hooks/useAuth"
import { TOOLKIT_CATEGORIES, TOOLKIT_TOOLS, usedToolkitCategories } from "../data/travelToolkit"

/**
 * Travel Toolkit — /travel-toolkit
 *
 * One organised home for every tool in the product. Before this page the 40+
 * features were only reachable from three different menus and a footer, so
 * there was no single place to see what the app can do.
 *
 * Three layers, lightest first:
 *   1. find-as-you-type over name, description and synonyms
 *   2. a category rail that narrows the list
 *   3. an "overview" mode that additionally surfaces recommended, recently
 *      used and favourited tools, all computed locally by useToolkitState
 *
 * Nothing here calls the network — the hub has to work offline and on a slow
 * connection, so it renders instantly from the registry.
 */

const GRID = "grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"

const SectionHead = ({ icon: Icon, title, hint, action }) => (
  <div className="mb-3 flex items-end justify-between gap-3">
    <div className="flex items-center gap-2">
      {Icon && (
        <span className="grid h-7 w-7 place-items-center rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] text-[var(--ny-green-dark)]" aria-hidden="true">
          <Icon size={15} />
        </span>
      )}
      <div>
        <h2 className="m-0 text-base font-bold text-[var(--ny-text)]">{title}</h2>
        {hint && <p className="m-0 text-xs text-[var(--ny-text-muted)]">{hint}</p>}
      </div>
    </div>
    {action}
  </div>
)

const Stat = ({ value, label, icon: Icon }) => (
  <div className="flex items-center gap-3 rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] px-4 py-3">
    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] text-[var(--ny-green-dark)]" aria-hidden="true">
      <Icon size={17} />
    </span>
    <div className="min-w-0">
      <p className="m-0 text-lg font-extrabold leading-none text-[var(--ny-text)]">{value}</p>
      <p className="m-0 truncate text-[0.72rem] uppercase tracking-wide text-[var(--ny-text-muted)]">{label}</p>
    </div>
  </div>
)

export default function TravelToolkit() {
  const { isAuthenticated } = useAuth()
  const [query, setQuery] = useState("")
  const [activeCat, setActiveCat] = useState("all")
  const searchRef = useRef(null)
  const debouncedQuery = useDebounce(query, 180)

  const {
    favouriteTools, isFavourite, toggleFavourite,
    recentTools, trackVisit, clearRecents,
    recommendations, stats,
  } = useToolkitState({ authenticated: isAuthenticated })

  useSeo({
    title: "Travel Toolkit | Nepal Yatra",
    description:
      "Every trip-planning tool in one organised place: itinerary builder, budget estimator, navigation, nearby services, safety alerts, translation and more.",
    path: "/travel-toolkit",
  })

  // "/" focuses search — but never while the traveller is typing in a field.
  useEffect(() => {
    const onKey = (event) => {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return
      const el = document.activeElement
      const typing = el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)
      if (typing) return
      event.preventDefault()
      searchRef.current?.focus()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  const visibleTools = useMemo(
    () => TOOLKIT_TOOLS.filter((tool) => isAuthenticated || !tool.authOnly),
    [isAuthenticated]
  )

  const trimmed = debouncedQuery.trim().toLowerCase()
  const results = useMemo(() => {
    if (!trimmed) return null
    return visibleTools.filter((tool) =>
      tool.label.toLowerCase().includes(trimmed) ||
      tool.blurb.toLowerCase().includes(trimmed) ||
      tool.tags.some((tag) => tag.includes(trimmed))
    )
  }, [trimmed, visibleTools])

  const categories = useMemo(() => usedToolkitCategories(isAuthenticated), [isAuthenticated])
  const catTools = useMemo(
    () => (activeCat === "all" ? [] : visibleTools.filter((t) => t.category === activeCat)),
    [activeCat, visibleTools]
  )

  const shownFavourites = favouriteTools.filter((t) => isAuthenticated || !t.authOnly)
  const overview = !trimmed && activeCat === "all"

  const handleOpen = (id) => trackVisit(id)

  const renderGrid = (tools) => (
    <div className={GRID}>
      {tools.map((tool) => (
        <ToolkitCard
          key={tool.id}
          tool={tool}
          showCategory
          favourite={isFavourite(tool.id)}
          onToggleFavourite={toggleFavourite}
          onOpen={handleOpen}
        />
      ))}
    </div>
  )

  return (
    <div className="container-app section-space min-h-[70vh] pb-16">
      <PageHeader
        icon={FiGrid}
        eyebrow="Organise"
        title="Travel Toolkit"
        subtitle="Every tool the app has, in one organised place. Search it, star the ones you use, and the hub learns what you need next."
      />

      <CMSPageIntro pageKey="travel-toolkit" />

      {/* ---- stats ---- */}
      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat value={stats.tools} label="Tools" icon={FiGrid} />
        <Stat value={categories.length} label="Categories" icon={FiZap} />
        <Stat value={stats.favourites} label="Favourites" icon={FiStar} />
        <Stat value={stats.recent} label="Recently used" icon={FiClock} />
      </div>

      {/* ---- search ---- */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <FiSearch size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" />
          <input
            ref={searchRef}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search tools — try “visa”, “taxi”, “SOS”, “nearby”…"
            aria-label="Search tools"
            data-testid="toolkit-search"
            className="w-full rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] py-3 pl-11 pr-10 text-sm text-[var(--ny-text)] outline-none transition placeholder:text-[var(--ny-text-muted)] focus:border-[var(--ny-green)] focus:ring-2 focus:ring-[var(--ny-green)]/25"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="absolute right-2.5 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-full text-[var(--ny-text-muted)] transition hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green-dark)]"
            >
              <FiX size={15} />
            </button>
          )}
        </div>
        <p className="hidden shrink-0 text-xs text-[var(--ny-text-muted)] lg:block">
          Press <kbd className="rounded border border-[var(--ny-border)] px-1.5 py-0.5 font-mono text-[0.7rem]">/</kbd> to search
        </p>
      </div>

      {/* ---- category rail ---- */}
      <div className="mb-6 flex flex-wrap gap-2" role="tablist" aria-label="Tool categories">
        <button
          type="button"
          role="tab"
          aria-selected={activeCat === "all"}
          onClick={() => setActiveCat("all")}
          className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
            activeCat === "all"
              ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white"
              : "border-[var(--ny-border)] bg-[var(--ny-white)] text-[var(--ny-text-secondary)] hover:border-[var(--ny-green)]"
          }`}
        >
          All
        </button>
        {categories.map((cat) => {
          const Icon = cat.icon
          const on = activeCat === cat.id
          return (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={on}
              onClick={() => setActiveCat(on ? "all" : cat.id)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
                on
                  ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white"
                  : "border-[var(--ny-border)] bg-[var(--ny-white)] text-[var(--ny-text-secondary)] hover:border-[var(--ny-green)]"
              }`}
            >
              <Icon size={13} aria-hidden="true" />
              {cat.label}
            </button>
          )
        })}
      </div>

      {/* ---- results ---- */}
      {trimmed ? (
        results.length ? (
          <section aria-labelledby="results-h">
            <SectionHead icon={FiSearch} title={`${results.length} result${results.length === 1 ? "" : "s"} for “${query.trim()}”`} />
            <div id="results-h">{renderGrid(results)}</div>
          </section>
        ) : (
          <EmptyState
            icon="search"
            title="No tool matches that"
            description={`Nothing here matches “${query.trim()}”. Try a category above, or clear the search to see everything.`}
            actionLabel="Clear search"
            onAction={() => setQuery("")}
          />
        )
      ) : activeCat !== "all" ? (
        <section aria-labelledby="cat-h">
          <SectionHead
            icon={(TOOLKIT_CATEGORIES.find((c) => c.id === activeCat) || {}).icon}
            title={(TOOLKIT_CATEGORIES.find((c) => c.id === activeCat) || {}).label}
            hint={(TOOLKIT_CATEGORIES.find((c) => c.id === activeCat) || {}).blurb}
          />
          <div id="cat-h">{catTools.length ? renderGrid(catTools) : <EmptyState title="Nothing here yet" description="This category has no tools available to you." />}</div>
        </section>
      ) : (
        <>
          {recommendations.length > 0 && (
            <section className="mb-8" aria-labelledby="rec-h">
              <SectionHead
                icon={FiZap}
                title="Recommended for you"
                hint="Ranked from your favourites and recent activity — computed on this device only."
              />
              <div id="rec-h">{renderGrid(recommendations.slice(0, 6))}</div>
            </section>
          )}

          {recentTools.length > 0 && (
            <section className="mb-8" aria-labelledby="recent-h">
              <SectionHead
                icon={FiClock}
                title="Continue where you left off"
                action={
                  <button
                    type="button"
                    onClick={clearRecents}
                    className="text-xs font-semibold text-[var(--ny-green)] underline-offset-2 hover:underline"
                  >
                    Clear
                  </button>
                }
              />
              <div id="recent-h">{renderGrid(recentTools.slice(0, 6))}</div>
            </section>
          )}

          {shownFavourites.length > 0 && (
            <section className="mb-8" aria-labelledby="fav-h">
              <SectionHead icon={FiStar} title="Your favourites" hint={`${shownFavourites.length} starred`} />
              <div id="fav-h">{renderGrid(shownFavourites)}</div>
            </section>
          )}

          {categories.map((cat) => {
            const tools = visibleTools.filter((t) => t.category === cat.id)
            if (!tools.length) return null
            const Icon = cat.icon
            return (
              <section key={cat.id} className="mb-8" aria-labelledby={`cat-${cat.id}`}>
                <SectionHead
                  icon={Icon}
                  title={cat.label}
                  hint={cat.blurb}
                  action={
                    <button
                      type="button"
                      onClick={() => setActiveCat(cat.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--ny-green)] underline-offset-2 hover:underline"
                    >
                      See all <FiChevronRight size={13} aria-hidden="true" />
                    </button>
                  }
                />
                <div id={`cat-${cat.id}`}>{renderGrid(tools)}</div>
              </section>
            )
          })}
        </>
      )}
    </div>
  )
}
