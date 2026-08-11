import { useState, useEffect } from "react"
import { FiDollarSign, FiPlus } from "react-icons/fi"
import adminApi from "../api/adminApi"
import TravelExpenditureForm from "../components/forms/TravelExpenditureForm"

export default function Expenditure() {
  const [reports, setReports] = useState([])
  const [showForm, setShowForm] = useState(false)

  const loadData = () => {
    adminApi.getExpenseFeedbacks().then(({ data }) => {
      setReports(data.results || data || [])
    }).catch(() => setReports([]))
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <div className="container-app py-8 space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 flex items-center gap-2">
            <FiDollarSign className="text-emerald-600" /> Travel Expenditure History
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Track your actual trip spending and train ML prediction models.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn-primary px-4 py-2 text-xs font-bold bg-purple-700 hover:bg-purple-800 text-white rounded-xl shadow"
        >
          <FiPlus /> {showForm ? "Close Form" : "Log Trip Expense"}
        </button>
      </div>

      {showForm && (
        <div className="card-base p-6 max-w-xl shadow-xl border border-purple-100 rounded-3xl">
          <TravelExpenditureForm onSuccess={() => { setShowForm(false); loadData(); }} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {reports.map((exp) => (
          <div key={exp.id} className="card-base p-5 shadow-lg border border-purple-100 rounded-2xl space-y-2">
            <div className="flex justify-between items-start">
              <h4 className="font-bold text-gray-900">{exp.destination_name}</h4>
              <span className="text-lg font-black text-purple-900">NPR {Number(exp.total_cost).toLocaleString()}</span>
            </div>
            <p className="text-xs text-gray-500">{exp.num_days} Days · {exp.num_people} Person(s) · {exp.travel_mode}</p>
            <div className="p-3 rounded-xl bg-purple-50 text-[11px] grid grid-cols-2 gap-1 text-gray-700">
              <div>🏨 Stay: NPR {exp.accommodation_cost}</div>
              <div>🚗 Transit: NPR {exp.travel_cost}</div>
              <div>🍛 Food: NPR {exp.food_cost}</div>
              <div>🎟️ Entry: NPR {exp.entry_cost}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
