import { useForm } from "react-hook-form"
import { useState } from "react"
import { motion } from "framer-motion"
import { FiDollarSign, FiHome, FiCoffee, FiTruck, FiShield, FiMap } from "react-icons/fi"
import budgetApi from "../api/budgetApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"

// Emergency reserve isn't something the ML model computes at all — it's
// a suggested contingency buffer, calculated here on the frontend as a
// flat 10% of the total. Clearly labeled as an estimate in the UI so
// it's not confused with a real line item from the backend.
const EMERGENCY_RESERVE_RATE = 0.1

const CATEGORY_META = [
  { key: "accommodation", label: "Hotel", icon: FiHome, color: "text-himalaya-500 bg-himalaya-50" },
  { key: "food", label: "Food", icon: FiCoffee, color: "text-saffron-600 bg-saffron-50" },
  { key: "transport", label: "Transportation", icon: FiTruck, color: "text-forest-600 bg-forest-50" },
  { key: "local_transport", label: "Local Transport", icon: FiMap, color: "text-nepalred-500 bg-nepalred-50" },
]

const BudgetEstimator = () => {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()
  const [estimate, setEstimate] = useState(null)
  const { showToast } = useToast()

  const onSubmit = async (data) => {
    try {
      const { data: result } = await budgetApi.estimate(data)

      // FIXED: reading the REAL response fields from the ML service —
      // total_budget_usd/daily_cost_usd, not the nonexistent
      // `estimated_total`/`total` the page used to look for (which
      // always rendered as "$undefined"). See budgetApi.js for the
      // full trace of why.
      setEstimate({
        total: result.total_budget_usd ?? result.total ?? 0,
        daily: result.daily_cost_usd ?? 0,
        accommodation: result.accommodation ?? 0,
        food: result.food ?? 0,
        transport: result.transport ?? 0,
        local_transport: result.local_transport ?? 0,
      })
    } catch {
      showToast("Could not calculate estimate. Backend not connected.", "error")
    }
  }

  const emergencyReserve = estimate ? Math.round(estimate.total * EMERGENCY_RESERVE_RATE) : 0

  return (
    <div className="container-app py-10 grid grid-cols-1 lg:grid-cols-2 gap-8 fade-in">
      <div>
        <h1 className="section-title flex items-center gap-2">
          <FiDollarSign className="text-himalaya-500" /> Budget Estimator
        </h1>
        <p className="text-gray-500 text-sm mb-6">
          Plan your trip expenses across accommodation, food, transport and activities.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">Destination</label>
              <input className="input-field mt-1" placeholder="e.g. Pokhara" {...register("destination", { required: true })} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Number of Travelers</label>
              <input type="number" min={1} defaultValue={1} className="input-field mt-1" {...register("travelers", { required: true })} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Duration (days)</label>
              <input type="number" min={1} defaultValue={3} className="input-field mt-1" {...register("days", { required: true })} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Travel Style</label>
              <select className="input-field mt-1" {...register("style")}>
                <option value="budget">Budget</option>
                <option value="standard">Standard</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? "Calculating..." : "Estimate Budget"}
          </button>
        </form>
      </div>

      <div>
        {estimate ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="card-base p-6 text-center">
              <p className="text-sm text-gray-500">Estimated Total Cost</p>
              <p className="text-4xl font-extrabold text-himalaya-500 mt-1">${estimate.total}</p>
              {estimate.daily > 0 && (
                <p className="text-xs text-gray-400 mt-1">≈ ${estimate.daily}/day</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {CATEGORY_META.map(({ key, label, icon: Icon, color }) => (
                <div key={key} className="card-base p-4 flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${color}`}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">{label}</p>
                    <p className="font-bold text-dark">${estimate[key]}</p>
                  </div>
                </div>
              ))}

              <div className="card-base p-4 flex items-center gap-3 col-span-2 border border-dashed border-saffron-200">
                <div className="p-2.5 rounded-xl bg-saffron-50 text-saffron-600">
                  <FiShield size={18} />
                </div>
                <div>
                  <p className="text-xs text-gray-400">
                    Emergency Reserve <span className="text-gray-300">(suggested 10% buffer, not from the model)</span>
                  </p>
                  <p className="font-bold text-dark">${emergencyReserve}</p>
                </div>
              </div>
            </div>

            <PieChartCard
              title="Cost Breakdown"
              labels={["Accommodation", "Food", "Transport", "Local Transport"]}
              data={[
                estimate.accommodation,
                estimate.food,
                estimate.transport,
                estimate.local_transport,
              ]}
            />
          </motion.div>
        ) : (
          <div className="card-base p-10 text-center text-gray-400 h-full flex items-center justify-center">
            Fill in the form to see your budget breakdown here.
          </div>
        )}
      </div>
    </div>
  )
}

export default BudgetEstimator