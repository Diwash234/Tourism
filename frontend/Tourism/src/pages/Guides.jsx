import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiSearch, FiMapPin, FiAward, FiStar, FiRefreshCw } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import workforceApi from "../api/workforceApi"

const LANGUAGES = ["Nepali", "English", "Hindi", "Japanese", "Chinese", "French", "German", "Spanish", "Korean"]

/**
 * Public directory of VERIFIED tourism guides (workforce spec §2/§10).
 * Only verified, publicly-listed profiles are ever returned by the API —
 * the listing is scoped server-side, not filtered in React.
 */
export default function Guides() {
  const [data, setData] = useState({ count: 0, results: [] })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState("")
  const [language, setLanguage] = useState("")
  const [region, setRegion] = useState("")

  const load = useCallback(() => {
    setLoading(true)
    workforceApi.guides({ q: q || undefined, language: language || undefined, region: region || undefined })
      .then(({ data: d }) => setData(d))
      .catch(() => setData({ count: 0, results: [] }))
      .finally(() => setLoading(false))
  }, [q, language, region])

  useEffect(() => {
    const t = setTimeout(() => load(), 250)
    return () => clearTimeout(t)
  }, [load])

  return (
    <div className="min-h-screen bg-[#F7F8F5]">
      <PageHeader
        title="Verified Local Guides"
        subtitle="Government-licensed, platform-verified guides across Nepal — trekking, cultural, wildlife and city specialists."
      />
      <div className="max-w-6xl mx-auto px-4 pb-16 -mt-6">
        <div className="bg-white rounded-3xl border shadow-sm p-4 flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search guides by name, skill or city…"
              aria-label="Search guides"
              className="w-full pl-10 pr-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"
            />
          </div>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} aria-label="Filter by language" className="px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]">
            <option value="">Any language</option>
            {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
          </select>
          <input
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="Region / district"
            aria-label="Filter by region"
            className="px-3 py-2.5 rounded-xl border text-sm w-full md:w-44 focus:outline-none focus:border-[#1D5146]"
          />
          <button onClick={load} className="px-4 py-2.5 bg-[#1D5146] text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Search
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 mt-6 mb-3">
          <p className="text-sm text-slate-600"><b>{data.count}</b> verified guide{data.count === 1 ? "" : "s"} available</p>
          <Link to="/guide-portal" className="text-sm font-bold text-[#1D5146] hover:underline">
            Become a guide →
          </Link>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((g) => (
            <div key={g.id} className="bg-white rounded-3xl border shadow-sm p-5 flex flex-col gap-2 hover:shadow-md transition">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-black text-slate-900">{g.name}</h3>
                  <p className="text-xs text-slate-500">{g.headline || "Tourism guide"}</p>
                </div>
                <span className="text-[10px] px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 font-black flex items-center gap-1 whitespace-nowrap">
                  <FiAward /> VERIFIED
                </span>
              </div>
              <p className="text-xs text-slate-600 line-clamp-3">{g.bio || "No bio provided yet."}</p>
              <div className="text-[11px] text-slate-500 space-y-1 mt-auto">
                {g.base_city && <p className="flex items-center gap-1"><FiMapPin /> {g.base_city}</p>}
                {g.languages?.length > 0 && <p>🗣️ {g.languages.join(", ")}</p>}
                {g.specializations?.length > 0 && <p>⭐ {g.specializations.join(", ")}</p>}
                {g.years_experience > 0 && <p>📅 {g.years_experience} years experience</p>}
              </div>
              <div className="flex items-center justify-between pt-2 border-t mt-2">
                <span className="text-sm font-black text-[#1D5146]">
                  {g.daily_rate_npr ? `NPR ${Number(g.daily_rate_npr).toLocaleString()}/day` : "Rate on request"}
                </span>
                {g.verified_at && (
                  <span className="text-[10px] text-slate-400">Verified {new Date(g.verified_at).toLocaleDateString()}</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {!loading && !data.results.length && (
          <div className="bg-white rounded-3xl border p-12 text-center mt-4">
            <FiStar className="mx-auto text-3xl text-slate-300" />
            <p className="text-slate-600 font-bold mt-2">No verified guides match this search yet.</p>
            <p className="text-xs text-slate-400 mt-1">Try removing filters — or apply to become Nepal&apos;s next verified guide.</p>
            <Link to="/guide-portal" className="inline-block mt-4 px-5 py-2.5 bg-[#1D5146] text-white rounded-xl text-sm font-bold">
              Apply as a Guide
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
