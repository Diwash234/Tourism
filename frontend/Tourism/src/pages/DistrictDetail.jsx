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

  useSeo({
    title: data ? `${data.district} District | ${data.province} Province, Nepal` : "District | Nepal Tourism",
    description: data
      ? `${data.public_destinations} verified destination${data.public_destinations === 1 ? "" : "s"} in ${data.district} district, ${data.province} province, Nepal — cities, top places and emergency services.`
      : "",
    path: districtName ? `/districts/${districtName}` : undefined,
  })

  useEffect(() => {
    let cancelled = false
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
    return () => { cancelled = true }
  }, [districtName])

  // While a newly requested district is still loading, never show the
  // previous district's content (also avoids synchronous setState in the
  // effect, which the react-hooks lint rule rejects).
  const stale = data && data.district?.toLowerCase() !== districtName?.toLowerCase()

  if (error) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3 text-center px-4">
        <p className="text-rose-300 font-semibold">{error}</p>
        <Link to="/districts" className="text-emerald-300 underline text-sm">
          Browse all districts
        </Link>
      </div>
    )
  }
  if (!data || stale) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-emerald-300">
        Loading district…
      </div>
    )
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <header>
        <p className="text-xs uppercase tracking-widest text-emerald-400">
          {data.province} Province
        </p>
        <h1 className="text-3xl font-bold text-white">{data.district} District</h1>
        <p className="text-slate-300 mt-1">
          {data.public_destinations} verified destination
          {data.public_destinations === 1 ? "" : "s"} in the database
        </p>
        {data.note && (
          <p className="mt-2 text-amber-300 text-sm border border-amber-500/30 rounded-lg px-3 py-2">
            {data.note}
          </p>
        )}
      </header>

      {data.cities?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-2">
            Cities / local areas
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.cities.map((c) => (
              <span
                key={c.name}
                className="px-3 py-1 rounded-full bg-slate-800 text-slate-200 text-sm"
              >
                {c.name}{" "}
                <span className="text-emerald-400">({c.destinations})</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {data.categories?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-2">
            Things to do — by category
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.categories.map((c) => (
              <span
                key={c.name}
                className="px-3 py-1 rounded-full bg-emerald-900/40 text-emerald-200 text-sm"
              >
                {c.name} <span className="text-emerald-400">({c.destinations})</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {data.top_destinations?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-3">
            Top destinations
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.top_destinations.map((d) => (
              <Link
                key={d.slug}
                to={`/destinations/${d.slug}`}
                className="block rounded-xl bg-slate-800/70 border border-slate-700 p-4 hover:border-emerald-500 transition"
              >
                <p className="font-semibold text-white">{d.name}</p>
                <p className="text-xs text-emerald-400 mt-0.5">
                  {d.category || "Attraction"}
                  {d.average_rating ? ` · ★ ${d.average_rating.toFixed(1)}` : ""}
                </p>
                {d.short_description && (
                  <p className="text-sm text-slate-300 mt-2 line-clamp-2">
                    {d.short_description}
                  </p>
                )}
                {d.latitude != null && (
                  <p className="text-xs text-slate-400 mt-2">
                    🧭 {d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}
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
            <h2 className="text-lg font-semibold text-white mb-2">
              Hospitals & health
            </h2>
            {data.hospitals?.length ? (
              <ul className="space-y-1 text-sm text-slate-200">
                {data.hospitals.map((h) => (
                  <li key={h.name}>
                    🏥 {h.name}
                    {h.phone ? <span className="text-slate-400"> · {h.phone}</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">
                No verified hospital records for this district yet.
              </p>
            )}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white mb-2">Police</h2>
            {data.police?.length ? (
              <ul className="space-y-1 text-sm text-slate-200">
                {data.police.map((p) => (
                  <li key={p.name}>
                    🚔 {p.name}
                    {p.phone ? <span className="text-slate-400"> · {p.phone}</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">
                No verified police records for this district yet.
              </p>
            )}
          </div>
        </section>
      )}

      <p className="text-xs text-slate-500">
        District page generated live from the tourism database — admin
        publications appear here immediately.
      </p>
    </main>
  )
}
