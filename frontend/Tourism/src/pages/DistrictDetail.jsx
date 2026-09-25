import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import axiosClient from "../api/axiosClient"
import useSeo from "../hooks/useSeo"

/**
 * Public district page — 100% database-driven (§16/§17).
 * Overview, cities/local areas, categories, top destinations and
 * emergency services all come from /api/v1/districts/<name>/; nothing
 * is hard-coded and empty districts say so honestly.
 */
export default function DistrictDetail() {
  const { districtName } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState("")
  const [retry, setRetry] = useState(0)

  useSeo({
    title: data ? `${data.district} District | ${data.province} Province, Nepal` : "District | Nepal Tourism",
    description: data
      ? `${data.public_destinations != null ? `${data.public_destinations} recorded destination${data.public_destinations === 1 ? "" : "s"}` : "Destination count unavailable"} in ${data.district} district, ${data.province} province, Nepal — cities, top places and emergency services.`
      : "",
    path: districtName ? `/districts/${districtName}` : undefined,
  })

  useEffect(() => {
    let cancelled = false
    const resetTimer = setTimeout(() => {
      if (cancelled) return
      setData(null)
      setError("")
    }, 0)
    axiosClient
      .get(`/districts/${encodeURIComponent(districtName)}/`)
      .then((res) => {
        if (cancelled) return
        setError("")
        setData(res.data)
      })
      .catch((err) => {
        if (cancelled) return
        setData(null)
        setError(
          err?.response?.status === 404
            ? err.response.data?.detail || "District not found."
            : "Could not load district data right now."
        )
      })
    return () => { cancelled = true; clearTimeout(resetTimer) }
  }, [districtName, retry])

  // While a newly requested district is still loading, never show the
  // previous district's content (also avoids synchronous setState in the
  // effect, which the react-hooks lint rule rejects).
  const stale = data && data.district?.toLowerCase() !== districtName?.toLowerCase()

  if (error) {
    return (
      <div className="ny-page container-app flex min-h-[60vh] flex-col items-center justify-center gap-3 px-4 text-center">
        <p className="font-semibold text-[var(--ny-danger)]">{error}</p>
        <div className="flex flex-wrap justify-center gap-3">
          <button type="button" onClick={() => setRetry((value) => value + 1)} className="ny-btn ny-btn-secondary">Try again</button>
          <Link to="/districts" className="text-sm text-[var(--ny-green)] underline">
            Browse all districts
          </Link>
        </div>
      </div>
    )
  }
  if (!data || stale) {
    return (
      <div className="ny-page container-app flex min-h-[60vh] items-center justify-center text-[var(--ny-text-secondary)]">
        Loading district…
      </div>
    )
  }

  return (
    <div className="ny-page container-app max-w-6xl space-y-8 py-6 sm:py-8">
      <header>
        <p className="ny-kicker">
          {data.province} Province
        </p>
        <h1 className="!text-3xl !text-[var(--ny-text)]">{data.district} District</h1>
        <p className="text-[var(--ny-text-secondary)] mt-1">
          {data.public_destinations != null ? `${data.public_destinations} recorded destination${data.public_destinations === 1 ? "" : "s"} in the catalogue` : "Destination count unavailable"}
        </p>
        {data.note && (
          <p className="mt-2 rounded-[var(--ny-radius-md)] border border-[#E9D39A] bg-[var(--ny-soft-gold)] px-3 py-2 text-sm text-[var(--ny-warning)]">
            {data.note}
          </p>
        )}
      </header>

      {data.cities?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--ny-text)] mb-2">
            Cities / local areas
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.cities.map((c) => (
              <span
                key={c.name}
                className="rounded-full border border-[var(--ny-border)] bg-white px-3 py-1 text-sm text-[var(--ny-text-secondary)]"
              >
                {c.name}{" "}
                <span className="text-emerald-400">({c.destinations ?? "Unavailable"})</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {data.categories?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--ny-text)] mb-2">
            Things to do — by category
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.categories.map((c) => (
              <span
                key={c.name}
                className="rounded-full border border-[var(--ny-border)] bg-[var(--ny-soft-green)] px-3 py-1 text-sm text-[var(--ny-green-dark)]"
              >
                {c.name} <span className="text-emerald-400">({c.destinations ?? "Unavailable"})</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {data.top_destinations?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-[var(--ny-text)] mb-3">
            Top destinations
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.top_destinations.map((d) => (
              <Link
                key={d.slug}
                to={`/destinations/${d.slug}`}
                className="ny-card block p-4 transition hover:-translate-y-1"
              >
                <p className="font-semibold text-[var(--ny-text)]">{d.name}</p>
                <p className="text-xs text-emerald-400 mt-0.5">
                  {d.category || "Attraction"}
                  {d.average_rating != null && Number.isFinite(Number(d.average_rating)) ? ` · ★ ${Number(d.average_rating).toFixed(1)}` : ""}
                </p>
                {d.short_description && (
                  <p className="text-sm text-[var(--ny-text-secondary)] mt-2 line-clamp-2">
                    {d.short_description}
                  </p>
                )}
                {d.latitude != null && d.longitude != null && Number.isFinite(Number(d.latitude)) && Number.isFinite(Number(d.longitude)) && (
                  <p className="text-xs text-[var(--ny-text-muted)] mt-2">
                    Coordinates: {Number(d.latitude).toFixed(4)}, {Number(d.longitude).toFixed(4)}
                  </p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {(data.hospitals?.length > 0 || data.police?.length > 0) && (
        <section className="grid md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-lg font-semibold text-[var(--ny-text)] mb-2">
              Hospitals & health
            </h2>
            {data.hospitals?.length ? (
              <ul className="space-y-1 text-sm text-[var(--ny-text-secondary)]">
                {data.hospitals.map((h) => (
                  <li key={h.name}>
                    Hospital: {h.name}
                    {h.phone ? <span className="text-[var(--ny-text-muted)]"> · {h.phone}</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--ny-text-muted)]">
                No recorded hospital records for this district yet.
              </p>
            )}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[var(--ny-text)] mb-2">Police</h2>
            {data.police?.length ? (
              <ul className="space-y-1 text-sm text-[var(--ny-text-secondary)]">
                {data.police.map((p) => (
                  <li key={p.name}>
                    Police: {p.name}
                    {p.phone ? <span className="text-[var(--ny-text-muted)]"> · {p.phone}</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--ny-text-muted)]">
                No recorded police records for this district yet.
              </p>
            )}
          </div>
        </section>
      )}

    </div>
  )
}
