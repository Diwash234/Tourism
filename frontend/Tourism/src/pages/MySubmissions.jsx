import { useState, useEffect } from "react"
import { FiMapPin, FiCheckCircle, FiClock, FiXCircle } from "react-icons/fi"
import destinationApi from "../api/destinationApi"

export default function MySubmissions() {
  const [submissions, setSubmissions] = useState([])

  useEffect(() => {
    destinationApi.getAll({ is_user_submitted: true }).then(({ data }) => {
      setSubmissions(data.results || data || [])
    }).catch(() => setSubmissions([]))
  }, [])

  return (
    <div className="container-app py-8 space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-3xl font-black text-gray-900 flex items-center gap-2">
          <FiMapPin className="text-[#102A2E]" /> My Place Submissions & Status
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Review places you suggested to the community and track their Admin Verification status.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {submissions.map((p) => {
          const isApproved = p.status === "approved"
          return (
            <div key={p.id} className="card-base p-5 shadow-lg border border-[#E5E0D5] rounded-2xl space-y-3">
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-gray-900 text-base">{p.name}</h4>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                  isApproved ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                }`}>
                  {isApproved ? "Approved ✓" : "Pending Review"}
                </span>
              </div>
              <p className="text-xs text-gray-500">📍 {p.city || p.district}, Nepal</p>
              <p className="text-xs text-gray-700 line-clamp-2">{p.description}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
