import { useEffect, useMemo, useState } from "react"
import useSeo from "../hooks/useSeo"
import { Link } from "react-router-dom"
import axiosClient from "../api/axiosClient"

const STATUS_LABEL = {
  well_covered: "Well covered",
  partially_covered: "Partially covered",
  limited_data: "Limited data",
  no_verified_data: "No verified data yet",
}

/** All 77 districts with real coverage counts from the database (§15). */
export default function DistrictsIndex() {
  useSeo({
    title: "All 77 Districts of Nepal | Browse by Province",
    description: "Explore every district of Nepal by province with verified tourism coverage — destinations, cities, hospitals and police from the live database.",
    path: "/districts",
  })
  const [data, setData] = useState(null)
  const [error, setError] = useState("")
  const [province, setProvince] = useState("All")

  useEffect(() => {
    axiosClient
      .get("/districts/")
      .then((res) => setData(res.data))
      .catch(() => setError("Could not load districts right now."))
  }, [])

  const rows = useMemo(() => {
    if (!data) return []
    return province === "All"
      ? data.districts
      : data.districts.filter((d) => d.province === province)
  }, [data, province])

  if (error) return <p className="p-8 text-rose-300">{error}</p>
  if (!data)
    return (
      <p className="p-8 text-emerald-300">Loading Nepal's 77 districts…</p>
    )

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white">Explore Nepal by district</h1>
      <p className="text-slate-300 mt-1 text-sm">
        {data.count} districts · coverage reflects verified database records
        only — nothing is artificially populated.
      </p>

      <div className="flex flex-wrap gap-2 mt-4">
        {["All", ...Object.keys(data.provinces)].map((p) => (
          <button
            key={p}
            onClick={() => setProvince(p)}
            className={`px-3 py-1 rounded-full text-sm border ${
              province === p
                ? "bg-emerald-600 border-emerald-500 text-white"
                : "bg-slate-800 border-slate-700 text-slate-300"
            }`}
          >
            {p}
            {p !== "All" && (
              <span className="text-emerald-300 ml-1">
                ({data.provinces[p]})
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-6">
        {rows.map((d) => (
          <Link
            key={d.name}
            to={`/districts/${encodeURIComponent(d.name)}`}
            className="rounded-xl bg-slate-800/70 border border-slate-700 p-4 hover:border-emerald-500 transition"
          >
            <p className="font-semibold text-white">{d.name}</p>
            <p className="text-xs text-slate-400">{d.province} Province</p>
            <p className="text-sm text-emerald-300 mt-1">
              {d.public_destinations} destinations ·{" "}
              {STATUS_LABEL[d.coverage_status] || d.coverage_status}
            </p>
          </Link>
        ))}
      </div>
    </main>
  )
}
