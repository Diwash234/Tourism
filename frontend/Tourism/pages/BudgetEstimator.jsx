import { useForm } from "react-hook-form"
import { useState } from "react"
import { FiDollarSign } from "react-icons/fi"
import budgetApi from "../api/budgetApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"

const BudgetEstimator = () => {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()
  const [estimate, setEstimate] = useState(null)
  const { showToast } = useToast()

  const onSubmit = async (data) => {
    try {
      const { data: result } = await budgetApi.estimate(data)
      setEstimate(result)
    } catch {
      showToast("Could not calculate estimate. Backend not connected.", "error")
    }
  }

  return (
    <div className="container-app py-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <h1 className="section-title flex items-center gap-2"><FiDollarSign className="text-primary-500" /> Budget Estimator</h1>
        <p className="text-gray-500 text-sm mb-6">Plan your trip expenses across accommodation, food, transport and activities.</p>

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
          <div className="space-y-6">
            <div className="card-base p-6 text-center">
              <p className="text-sm text-gray-500">Estimated Total Cost</p>
              <p className="text-4xl font-extrabold text-primary-500 mt-1">${estimate.total}</p>
            </div>
            <PieChartCard
              title="Cost Breakdown"
              labels={["Accommodation", "Food", "Transport", "Activities"]}
              data={[
                estimate.accommodation || 0,
                estimate.food || 0,
                estimate.transport || 0,
                estimate.activities || 0,
              ]}
            />
          </div>
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