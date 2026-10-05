import { useEffect, useState } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import { FiMapPin, FiClock, FiNavigation, FiAlertCircle, FiHeart } from "react-icons/fi"
import axiosClient from "../api/axiosClient"

/**
 * Travel Guide page — renders a curated multi-day itinerary with real
 * hotel, hospital and attraction data from the backend.
 *
 * URL: /travel-guides/15-day-pokhara
 * City selector: dropdown to switch between all 200 city guides.
 */
export default function TravelGuidePage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [guide, setGuide] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [activeDay, setActiveDay] = useState(1)
  const [allGuides, setAllGuides] = useState([])

  // Load all guides for the city selector
  useEffect(() => {
    axiosClient.get("/travel-guides/")
      .then(({ data }) => setAllGuides(data || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    setError("")
    axiosClient.get(`/travel-guides/${encodeURIComponent(slug)}/`)
      .then(({ data }) => {
        setGuide(data)
        setLoading(false)
      })
      .catch(() => {
        setError("Could not load the travel guide.")
        setLoading(false)
      })
  }, [slug])

  if (loading) return <div className="ny-page container-app py-12 text-center text-gray-500">Loading guide…</div>
  if (error) return <div className="ny-page container-app py-12 text-center text-red-600">{error}</div>
  if (!guide) return null

  const day = guide.days.find((d) => d.day_number === activeDay)

  return (
    <div className="ny-page container-app py-6 sm:py-8 space-y-8">
      {/* City selector */}
      {allGuides.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="city-select" className="text-sm font-semibold text-gray-700">Select a city:</label>
          <select
            id="city-select"
            value={slug || ""}
            onChange={(e) => {
              if (e.target.value) {
                setActiveDay(1)
                navigate(`/travel-guides/${encodeURIComponent(e.target.value)}`)
              }
            }}
            className="input-field min-h-11 max-w-xs"
          >
            {allGuides.map((g) => (
              <option key={g.slug} value={g.slug}>
                {g.destination_name} ({g.days_count} days)
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Header */}
      <header className="max-w-3xl">
        <span className="ny-kicker">{guide.destination.name}</span>
        <h1 className="mt-2 text-3xl sm:text-4xl font-black text-gray-900">{guide.title}</h1>
        <p className="mt-3 text-gray-600 leading-relaxed">{guide.subtitle}</p>
        <p className="mt-3 text-sm text-amber-800">Planning outline only: confirm transport, access, weather, opening hours, and bookings with local operators before travel.</p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1.5"><FiClock size={14} /> {guide.days_count} days</span>
          <span className="flex items-center gap-1.5"><FiMapPin size={14} /> {guide.pace}</span>
          {guide.best_for && <span className="flex items-center gap-1.5"><FiHeart size={14} /> {guide.best_for}</span>}
        </div>
      </header>

      {/* Day tabs */}
      <div className="ny-horizontal-scroll flex gap-2 pb-2" role="tablist" aria-label="Itinerary days">
        {guide.days.map((d) => (
          <button
            key={d.day_number}
            role="tab"
            aria-selected={activeDay === d.day_number}
            onClick={() => setActiveDay(d.day_number)}
            className={`min-h-10 whitespace-nowrap rounded-full border px-4 text-sm font-semibold transition ${
              activeDay === d.day_number
                ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white"
                : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)]"
            }`}
          >
            Day {d.day_number}
          </button>
        ))}
      </div>

      {/* Active day */}
      {day && (
        <div className="space-y-6">
          <div className="ny-panel p-5 sm:p-6">
            <h2 className="text-xl font-bold text-gray-900">Day {day.day_number}: {day.title}</h2>
            {day.route && (
              <p className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                <FiNavigation size={14} className="text-[var(--ny-green)]" />
                {day.route}
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-500">
              {day.travel_distance && <span>Distance: {day.travel_distance}</span>}
              {day.travel_time && <span>Time: {day.travel_time}</span>}
              {day.overnight_stay && <span>Overnight: {day.overnight_stay}</span>}
            </div>
          </div>

          {/* Schedule */}
          <div className="grid gap-4 md:grid-cols-3">
            {[
              { label: "Morning", content: day.morning },
              { label: "Afternoon", content: day.afternoon },
              { label: "Evening", content: day.evening },
            ].filter((s) => s.content).map((s) => (
              <div key={s.label} className="ny-panel p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ny-green)] mb-2">{s.label}</h3>
                <p className="text-sm text-gray-700 leading-relaxed">{s.content}</p>
              </div>
            ))}
          </div>

          {/* Practical notes */}
          {day.practical_notes && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 flex items-start gap-3">
              <FiAlertCircle size={18} className="mt-0.5 shrink-0" />
              <p>{day.practical_notes}</p>
            </div>
          )}

          {/* Hotels */}
          {day.hotels.length > 0 && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3">Nearby Hotels</h3>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {day.hotels.map((h) => (
                  <div key={h.id} className="ny-card p-4">
                    <h4 className="font-bold text-gray-900">{h.name}</h4>
                    {h.address && <p className="mt-1 text-xs text-gray-500 flex items-center gap-1"><FiMapPin size={12} />{h.address}</p>}
                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                      {h.price_per_night && <span>रू{h.price_per_night}/night</span>}
                      {h.rating && <span>★ {h.rating}</span>}
                      <span className={`px-2 py-0.5 rounded-full ${h.booking_status === "available" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}`}>{h.booking_status}</span>
                    </div>
                    {h.source_url && <a href={h.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-xs font-semibold text-[var(--ny-green)] hover:underline">Verify hotel details</a>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hospitals */}
          {day.hospitals.length > 0 && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3">Nearby Hospitals</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {day.hospitals.map((h) => (
                  <div key={h.id} className="ny-card p-4">
                    <h4 className="font-bold text-gray-900">{h.name}</h4>
                    {h.address && <p className="mt-1 text-xs text-gray-500">{h.address}</p>}
                    {h.phone && <p className="mt-1 text-xs text-[var(--ny-green)] font-medium">{h.phone}</p>}
                    {h.opening_hours && <p className="mt-1 text-xs text-gray-400">{h.opening_hours}</p>}
                    {h.source_url && <a href={h.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-xs font-semibold text-[var(--ny-green)] hover:underline">Verify hospital details</a>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attractions */}
          {day.attractions.length > 0 && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3">Attractions</h3>
              <div className="flex flex-wrap gap-2">
                {day.attractions.map((a) => (
                  <Link
                    key={a.id}
                    to={`/destinations/${a.slug}`}
                    className="inline-flex items-center gap-1.5 rounded-full border border-[var(--ny-border)] bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)] transition"
                  >
                    <FiMapPin size={13} />
                    {a.name}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
