import { useForm, useWatch } from "react-hook-form"
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import {
  FiDollarSign,
  FiHome,
  FiCoffee,
  FiTruck,
  FiShield,
  FiMap,
  FiLoader,
} from "react-icons/fi"

import budgetApi from "../api/budgetApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"

const EMERGENCY_RESERVE_RATE = 0.1

const CURRENCIES = {
  NPR: { symbol: "रू", rate: 133, label: "Nepali Rupee" },
  USD: { symbol: "$", rate: 1, label: "US Dollar" },
  INR: { symbol: "₹", rate: 83, label: "Indian Rupee" },
  EUR: { symbol: "€", rate: 0.92, label: "Euro" },
  GBP: { symbol: "£", rate: 0.79, label: "British Pound" },
}

const formatMoney = (usd, currency) => {
  const c = CURRENCIES[currency] || CURRENCIES.NPR
  const v = Math.round((Number(usd) || 0) * c.rate)
  return `${c.symbol}${v.toLocaleString()}`
}

const CATEGORY_META = [
  {
    key: "accommodation",
    label: "Hotel & Lodging",
    icon: FiHome,
    color: "text-yellow-600 bg-yellow-50",
  },
  {
    key: "food",
    label: "Food & Dining",
    icon: FiCoffee,
    color: "text-orange-600 bg-orange-50",
  },
  {
    key: "transport",
    label: "Transport & Transit",
    icon: FiTruck,
    color: "text-blue-600 bg-blue-50",
  },
]

const BudgetEstimator = () => {
  const {
    register,
    handleSubmit,
    control,
    formState: { isSubmitting },
  } = useForm({
    defaultValues: {
      destination: "Pokhara",
      travelers: 1,
      days: 3,
      style: "mid",
    },
  })

  const [estimate, setEstimate] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currency, setCurrency] = useState(
    () => localStorage.getItem("tourism_currency") || "NPR"
  )
  const { showToast } = useToast()
  const debounceRef = useRef(null)
  const requestRef = useRef(0)

  const watched = useWatch({ control })

  useEffect(() => {
    if (!watched?.destination) return

    if (debounceRef.current) clearTimeout(debounceRef.current)

    debounceRef.current = setTimeout(() => {
      calculate(watched)
    }, 500)

    return () => clearTimeout(debounceRef.current)
  }, [
    watched?.destination,
    watched?.travelers,
    watched?.days,
    watched?.style,
  ])

  const calculate = async (data) => {
    const requestId = ++requestRef.current
    setLoading(true)

    try {
      const { data: result } = await budgetApi.estimate(data)

      if (requestId !== requestRef.current) return

      const total = result.total_budget_usd ?? result.total ?? 0

      const daily =
        result.daily_cost_usd ??
        (total ? Math.round(total / (data.days || 3)) : 0)

      setEstimate({
        total,
        daily,
        source: result.baseline_source || result.transport_basis || "estimate",
        dataset: result.dataset || null,
        accommodation:
          result.breakdown?.accommodation ?? result.accommodation ?? 0,
        food: result.breakdown?.food ?? result.food ?? 0,
        transport:
          (result.breakdown?.transport ?? result.transport ?? 0) +
          (result.breakdown?.local_transport ?? result.local_transport ?? 0),
      })
    } catch (error) {
      if (requestId !== requestRef.current) return

      showToast(
        error.response?.data?.detail ||
          error.response?.data?.error ||
          "Could not calculate estimate. Backend not connected.",
        "error"
      )
    } finally {
      if (requestId === requestRef.current) setLoading(false)
    }
  }

  const onSubmit = (data) => {
    calculate(data)
  }

  const emergencyReserve = estimate
    ? Math.round(estimate.total * EMERGENCY_RESERVE_RATE)
    : 0

  return (
    <div className="container-app py-10 grid grid-cols-1 lg:grid-cols-2 gap-8 fade-in theme-orange">
      {/* FORM */}
      <div>
        <h1 className="section-title flex items-center gap-2">
          <FiDollarSign className="text-saffron-600" />
          Budget Estimator
        </h1>

        <p className="text-gray-500 text-sm mb-6">
          Plan your Nepal trip expenses. The estimate updates automatically when
          you change your trip details.
        </p>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="card-base p-6 space-y-4 shadow-md bg-white border border-slate-200"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                Destination
              </label>
              <input
                className="input-field mt-1"
                placeholder="e.g. Pokhara"
                {...register("destination", { required: true })}
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500">
                Number of Travelers
              </label>
              <input
                type="number"
                min={1}
                className="input-field mt-1"
                {...register("travelers", { required: true })}
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500">
                Duration (days)
              </label>
              <input
                type="number"
                min={1}
                className="input-field mt-1"
                {...register("days", { required: true })}
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500">
                Travel Style
              </label>
              <select className="input-field mt-1" {...register("style")}>
                <option value="budget">Budget</option>
                <option value="mid">Mid-range</option>
                <option value="standard">Standard</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || isSubmitting}
            className="btn-primary w-full"
          >
            {loading || isSubmitting ? "Calculating..." : "Estimate Budget"}
          </button>

          <div className="mt-4">
            <label className="text-xs font-medium text-gray-500">
              Display currency
            </label>
            <select
              className="input-field mt-1"
              value={currency}
              onChange={(e) => {
                setCurrency(e.target.value)
                localStorage.setItem("tourism_currency", e.target.value)
              }}
            >
              {Object.entries(CURRENCIES).map(([code, c]) => (
                <option key={code} value={code}>
                  {code} — {c.label} ({c.symbol})
                </option>
              ))}
            </select>
          </div>

          {loading && (
            <p className="flex items-center gap-2 text-xs text-saffron-600">
              <FiLoader className="animate-spin" />
              Updating estimate...
            </p>
          )}
        </form>
      </div>

      {/* RESULT */}
      <div>
        {estimate ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="card-base p-6 text-center bg-white border border-slate-200 shadow-md">
              <p className="text-sm text-gray-500">Estimated Total Cost</p>

              <p className="text-4xl font-extrabold text-saffron-600 my-1">
                {formatMoney(estimate.total, currency)}
              </p>

              <p className="text-xs text-gray-500">
                ≈ ${Math.round(estimate.total || 0).toLocaleString()} USD ·{" "}
                {formatMoney(estimate.total, currency)} {currency}
              </p>

              {estimate.source === "dataset_csv" ? (
                <p className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-green-800 bg-green-50 border border-green-200 px-3 py-1 rounded-full shadow-sm">
                  ✓ Based on real Nepal travel-cost dataset
                  {estimate.dataset
                    ? ` (${estimate.dataset.destinations}+ places)`
                    : ""}
                </p>
              ) : null}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {CATEGORY_META.map(({ key, label, icon: Icon, color }) => (
                <div key={key} className="card-base p-4 flex items-center gap-3 bg-white border border-slate-200 shadow-sm">
                  <div className={`p-2.5 rounded-xl ${color}`}>
                    <Icon size={18} />
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="font-bold text-dark text-sm">
                      {formatMoney(estimate[key], currency)}
                    </p>
                  </div>
                </div>
              ))}

              <div className="card-base p-4 flex items-center gap-3 sm:col-span-3 bg-slate-50 border border-slate-200">
                <div className="p-2.5 rounded-xl bg-amber-100 text-amber-800">
                  <FiShield size={18} />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Emergency Reserve (10%)</p>
                  <p className="font-bold text-dark text-sm">
                    {formatMoney(emergencyReserve, currency)}
                  </p>
                </div>
              </div>
            </div>

            <PieChartCard
              title="Cost Breakdown"
              labels={[
                "Accommodation",
                "Food & Dining",
                "Transport & Transit",
              ]}
              data={[
                estimate.accommodation,
                estimate.food,
                estimate.transport,
              ]}
            />
          </motion.div>
        ) : (
          <div className="card-base p-10 text-center text-gray-400 h-full flex items-center justify-center bg-white border border-slate-200">
            Fill in the form to see your budget breakdown here.
          </div>
        )}
      </div>
    </div>
  )
}

export default BudgetEstimator
