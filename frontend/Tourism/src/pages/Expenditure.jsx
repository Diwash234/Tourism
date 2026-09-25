import { useState, useEffect } from "react"
import PageHeader from "../components/common/PageHeader"
import { FiDollarSign, FiPlus } from "react-icons/fi"
import adminApi from "../api/adminApi"
import TravelExpenditureForm from "../components/forms/TravelExpenditureForm"
import EmptyState from "../components/common/EmptyState"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import SkeletonLoader from "../components/common/SkeletonLoader"

export default function Expenditure() {
  const [reports, setReports] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")

  const loadData = () => {
    setLoading(true)
    setLoadError("")
    adminApi.getExpenseFeedbacks().then(({ data }) => {
      setReports(data.results || data || [])
    }).catch(() => {
      setReports([])
      setLoadError("Travel expenditure records could not be loaded right now.")
    }).finally(() => setLoading(false))
  }

  useEffect(() => {
    const timer = setTimeout(loadData, 0)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <CMSPageIntro pageKey="expenditure" />
          <PageHeader title="Travel Expenditure History" icon={FiDollarSign} />
          <p className="text-gray-500 text-sm mt-1">
            Track the expenses you record for your trips. Values are shown exactly as entered or returned by the service.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn-primary px-4 py-2 text-xs font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow"
        >
          <FiPlus /> {showForm ? "Close Form" : "Log Trip Expense"}
        </button>
      </div>

      {showForm && (
        <div className="card-base p-6 max-w-xl shadow-xl border border-[#E5E0D5] rounded-3xl">
          <TravelExpenditureForm onSuccess={() => { setShowForm(false); loadData(); }} />
        </div>
      )}

      {loading && <SkeletonLoader count={3} type="card" />}
      {loadError && <div role="alert" className="ny-panel border-[#E9B9B9] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)]">{loadError} <button type="button" onClick={loadData} className="ml-2 font-semibold underline">Try again</button></div>}
      {!loading && !loadError && !showForm && reports.length === 0 && (
        <EmptyState
          icon={FiDollarSign}
          title="No trip expenses logged yet"
          subtitle="Log your first trip expense to see your spending history."
        />
      )}

      {!loading && !loadError && <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {reports.map((exp) => (
          <div key={exp.id} className="card-base p-5 shadow-lg border border-[#E5E0D5] rounded-2xl space-y-2">
            <div className="flex justify-between items-start">
              <h4 className="font-bold text-gray-900">{exp.destination_name}</h4>
              <span className="text-lg font-black text-[#102A2E]">{exp.total_cost != null ? `NPR ${Number(exp.total_cost).toLocaleString()}` : "Total unavailable"}</span>
            </div>
            <p className="text-xs text-gray-500">{exp.num_days} Days · {exp.num_people} Person(s) · {exp.travel_mode}</p>
            <div className="p-3 rounded-xl bg-[#F7F8F5] text-[11px] grid grid-cols-2 gap-1 text-gray-700">
              <div>Stay: {exp.accommodation_cost != null ? `NPR ${Number(exp.accommodation_cost).toLocaleString()}` : "unavailable"}</div>
              <div>Transit: {exp.travel_cost != null ? `NPR ${Number(exp.travel_cost).toLocaleString()}` : "unavailable"}</div>
              <div>Food: {exp.food_cost != null ? `NPR ${Number(exp.food_cost).toLocaleString()}` : "unavailable"}</div>
              <div>Entry: {exp.entry_cost != null ? `NPR ${Number(exp.entry_cost).toLocaleString()}` : "unavailable"}</div>
            </div>
          </div>
        ))}
      </div>}
    </div>
  )
}
