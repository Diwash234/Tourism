import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { FiMapPin } from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useSeo from "../hooks/useSeo"
import PageHeader from "../components/common/PageHeader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import SkeletonLoader from "../components/common/SkeletonLoader"
import EmptyState from "../components/common/EmptyState"
import ErrorState from "../components/ui/ErrorState"

const STATUS_LABEL = { well_covered: "Well covered", partially_covered: "Partially covered", limited_data: "Limited data", no_verified_data: "No verified data yet" }

export default function DistrictsIndex() {
  useSeo({ title: "All districts of Nepal | Browse by province", description: "Explore Nepal districts by province with recorded tourism coverage.", path: "/districts" })
  const [data, setData] = useState(null)
  const [error, setError] = useState("")
  const [province, setProvince] = useState("All")

  const load = () => {
    setError("")
    axiosClient.get("/districts/").then((response) => setData(response.data)).catch(() => setError("We couldn't load the district directory right now."))
  }
  useEffect(() => { const timer = setTimeout(load, 0); return () => clearTimeout(timer) }, [])

  const rows = useMemo(() => data?.districts?.filter((district) => province === "All" || district.province === province) || [], [data, province])
  if (error) return <div className="ny-page container-app py-10"><ErrorState message={error} onRetry={load} /></div>
  if (!data) return <div className="container-app space-y-6 py-8"><SkeletonLoader count={6} /></div>

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <Breadcrumbs items={[{ label: "Districts", to: "/districts" }]} />
      <PageHeader title="Explore Nepal by district" subtitle={`${data.count || data.districts?.length || 0} districts are available in the project directory. Coverage reflects recorded data, not a promise that every service is listed.`} icon={FiMapPin} />
      <div className="ny-horizontal-scroll flex gap-2 border-b border-[var(--ny-border)] pb-4" role="group" aria-label="Filter districts by province">{["All", ...Object.keys(data.provinces || {})].map((item) => <button key={item} type="button" onClick={() => setProvince(item)} className={`min-h-10 whitespace-nowrap rounded-full border px-3 text-sm font-semibold ${province === item ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white" : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)]"}`} aria-pressed={province === item}>{item}{item !== "All" && <span className="ml-1 text-xs opacity-80">({data.provinces[item]})</span>}</button>)}</div>
      {rows.length ? <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">{rows.map((district) => <Link key={district.name} to={`/districts/${encodeURIComponent(district.name)}`} className="ny-card flex flex-col p-5"><div className="flex items-start justify-between gap-3"><div><h2 className="font-bold">{district.name}</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{district.province} Province</p></div><FiMapPin size={18} className="text-[var(--ny-green)]" aria-hidden="true" /></div><p className="mt-4 text-sm text-[var(--ny-text-secondary)]">{district.public_destinations != null ? `${district.public_destinations} destinations` : "Destination count unavailable"} · {STATUS_LABEL[district.coverage_status] || district.coverage_status || "Coverage unavailable"}</p><span className="mt-5 text-sm font-semibold text-[var(--ny-green)]">View district →</span></Link>)}</div> : <EmptyState title="No districts match this province" subtitle="Try another province filter." />}
    </div>
  )
}
