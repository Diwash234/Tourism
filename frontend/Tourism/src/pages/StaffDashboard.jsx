import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  FiBriefcase, FiMapPin, FiCheckCircle, FiDollarSign, FiPlus,
  FiFileText, FiShield, FiTrendingUp, FiActivity, FiRefreshCw
} from "react-icons/fi"
import adminApi from "../api/adminApi"
import destinationApi from "../api/destinationApi"
import useToast from "../hooks/useToast"
import TravelExpenditureForm from "../components/forms/TravelExpenditureForm"
import RiskAssessmentForm from "../components/forms/RiskAssessmentForm"

export default function StaffDashboard() {
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState("feedbacks")
  const [pendingPlaces, setPendingPlaces] = useState([])
  const [pendingImages, setPendingImages] = useState([])
  const [expenseReports, setExpenseReports] = useState([])
  const [loading, setLoading] = useState(false)

  const loadStaffData = async () => {
    setLoading(true)
    try {
      const [pRes, iRes, eRes] = await Promise.allSettled([
        adminApi.getPendingPlaces(),
        adminApi.getPendingImages(),
        adminApi.getExpenseFeedbacks(),
      ])
      if (pRes.status === "fulfilled") setPendingPlaces(pRes.value.data)
      if (iRes.status === "fulfilled") setPendingImages(iRes.value.data)
      if (eRes.status === "fulfilled") setExpenseReports(eRes.value.data.results || eRes.value.data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStaffData()
  }, [])

  return (
    <div className="container-app py-8 space-y-6 animate-fadeIn">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-bold uppercase tracking-wider">
            Field Officer Portal
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
            <FiBriefcase className="text-purple-700" /> Staff & Sub-Admin Operations Desk
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Ground data collection, place verification, field surveys, and ML dataset entry.
          </p>
        </div>

        <button
          onClick={loadStaffData}
          className="px-4 py-2 rounded-xl bg-purple-50 text-purple-800 hover:bg-purple-100 text-xs font-bold flex items-center gap-1.5 border border-purple-200"
        >
          <FiRefreshCw className={loading ? "animate-spin" : ""} size={14} /> Refresh Tasks
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card-base p-5 shadow-md border border-purple-100 bg-purple-50/50">
          <p className="text-xs font-semibold text-gray-500 uppercase">Pending Verification</p>
          <p className="text-3xl font-black text-purple-950 mt-1">{pendingPlaces.length}</p>
          <span className="text-xs text-purple-700 font-medium">Places awaiting review</span>
        </div>

        <div className="card-base p-5 shadow-md border border-purple-100 bg-amber-50/50">
          <p className="text-xs font-semibold text-gray-500 uppercase">Photo Queue</p>
          <p className="text-3xl font-black text-amber-950 mt-1">{pendingImages.length}</p>
          <span className="text-xs text-amber-700 font-medium">Images awaiting verification</span>
        </div>

        <div className="card-base p-5 shadow-md border border-purple-100 bg-emerald-50/50">
          <p className="text-xs font-semibold text-gray-500 uppercase">Surveys Recorded</p>
          <p className="text-3xl font-black text-emerald-950 mt-1">{expenseReports.length}</p>
          <span className="text-xs text-emerald-700 font-medium">ML Ground data entries</span>
        </div>
      </div>

      <div className="flex gap-2 border-b pb-2">
        <button
          onClick={() => setActiveTab("feedbacks")}
          className={`px-4 py-2 rounded-xl text-xs font-bold ${
            activeTab === "feedbacks" ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700"
          }`}
        >
          💰 Log Field Expenditure (ML)
        </button>
        <button
          onClick={() => setActiveTab("risk")}
          className={`px-4 py-2 rounded-xl text-xs font-bold ${
            activeTab === "risk" ? "bg-purple-700 text-white" : "bg-gray-100 text-gray-700"
          }`}
        >
          🛡️ Field Safety & Hazard Survey
        </button>
      </div>

      {activeTab === "feedbacks" && (
        <div className="card-base p-6 sm:p-8 max-w-2xl shadow-xl border border-purple-100 rounded-3xl bg-white">
          <h3 className="font-bold text-base text-gray-900 mb-4 flex items-center gap-2">
            <FiDollarSign className="text-emerald-600" /> Record Field Survey Expenditure
          </h3>
          <TravelExpenditureForm onSuccess={loadStaffData} />
        </div>
      )}

      {activeTab === "risk" && (
        <div className="card-base p-6 sm:p-8 max-w-2xl shadow-xl border border-purple-100 rounded-3xl bg-white">
          <h3 className="font-bold text-base text-gray-900 mb-4 flex items-center gap-2">
            <FiShield className="text-purple-600" /> Record Field Safety & Hazard Report
          </h3>
          <RiskAssessmentForm onSuccess={loadStaffData} />
        </div>
      )}
    </div>
  )
}
