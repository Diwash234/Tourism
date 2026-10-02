import { useState, useEffect } from "react"
import PageHeader from "../components/common/PageHeader"
import { FiMapPin } from "react-icons/fi"
import destinationApi from "../api/destinationApi"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import EmptyState from "../components/common/EmptyState"
import ErrorState from "../components/ui/ErrorState"
import SkeletonLoader from "../components/common/SkeletonLoader"

export default function MySubmissions() {
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    destinationApi.getAll({ is_user_submitted: true }).then(({ data }) => {
      setSubmissions(data.results || data || [])
    }).catch((requestError) => {
      setError(requestError.response?.data?.detail || "We could not load your submissions right now.")
    }).finally(() => setLoading(false))
  }, [])

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <div>
        <CMSPageIntro pageKey="my-submissions" />
        <PageHeader title="My Place Submissions & Status" icon={FiMapPin} />
        <p className="text-gray-500 text-sm mt-1">
          Review places you suggested and track their review status.
        </p>
      </div>

      {loading ? <SkeletonLoader count={3} type="card" /> : error ? <ErrorState message={error} onRetry={() => window.location.reload()} /> : submissions.length === 0 ? <EmptyState title="No submissions yet" subtitle="Places you suggest will appear here with their current review status." /> : <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {submissions.map((p) => {
          const status = String(p.status || "").toLowerCase()
           const statusLabel = status === "approved" ? "Approved" : status === "rejected" ? "Not approved" : status === "archived" ? "Archived" : "Pending review"
          return (
            <div key={p.id} className="card-base p-5 shadow-lg border border-[#E5E0D5] rounded-2xl space-y-3">
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-gray-900 text-base">{p.name}</h4>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                  status === "approved" ? "bg-emerald-100 text-emerald-800" : status === "rejected" || status === "archived" ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                }`}>
                  {statusLabel}
                </span>
              </div>
              <p className="text-xs text-gray-500">{p.city || p.district ? `${p.city || p.district}, Nepal` : "Location unavailable"}</p>
              <p className="text-xs text-gray-700 line-clamp-2">{p.description}</p>
            </div>
          )
        })}
      </div>}
    </div>
  )
}
