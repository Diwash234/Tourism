import { useForm, useWatch } from "react-hook-form"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import {
  FiDollarSign,
  FiHome,
  FiCoffee,
  FiTruck,
  FiShield,
  FiCompass,
  FiShoppingBag,
  FiLoader,
} from "react-icons/fi"

import budgetApi from "../api/budgetApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"

const CURRENCIES = {
  NPR: { symbol: "रू", label: "Nepali Rupee" },
  USD: { symbol: "$", label: "US Dollar" },
  INR: { symbol: "₹", label: "Indian Rupee" },
  EUR: { symbol: "€", label: "Euro" },
  GBP: { symbol: "£", label: "British Pound" },
}

const formatMoney = (amount, currency) => {
  if (amount == null || !Number.isFinite(Number(amount))) return "Unavailable"
  const c = CURRENCIES[currency]
  if (!c) return "Unavailable"
  return `${c.symbol}${Math.round(Number(amount)).toLocaleString()}`
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
  {
    key: "activities",
    label: "Sightseeing & Activities",
    icon: FiCompass,
    color: "text-emerald-700 bg-[#F7F8F5]",
  },
  {
    key: "shopping",
    label: "Local Shopping & Souvenirs",
    icon: FiShoppingBag,
    color: "text-emerald-600 bg-emerald-50",
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
      destination: "",
      travelers: 1,
      days: 3,
      style: "mid",
    },
  })

  const [estimate, setEstimate] = useState(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [currency, setCurrency] = useState(
    () => localStorage.getItem("tourism_currency") || "USD"
  )
  const { showToast } = useToast()
  const debounceRef = useRef(null)
  const requestRef = useRef(0)
  const abortRef = useRef(null)

  const watched = useWatch({ control })

  useEffect(() => {
    if (!watched?.destination?.trim()) {
      const clearTimer = setTimeout(() => { setEstimate(null); setLoading(false) }, 0)
      return () => clearTimeout(clearTimer)
    }

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

  async function calculate(data) {
    const requestId = ++requestRef.current
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError("")
    setEstimate(null)

    try {
      const { data: result } = await budgetApi.estimate(data, { signal: controller.signal })

      if (requestId !== requestRef.current) return

      const totalUsd = result.total_budget_usd ?? result.total ?? result.estimated_total ?? null
      const dailyUsd = result.daily_cost_usd ?? (totalUsd != null ? Math.round(totalUsd / (data.days || 3)) : null)
      const totalNpr = result.total_budget_npr ?? null
      const dailyNpr = result.daily_budget_npr ?? (totalNpr != null ? Math.round(totalNpr / (data.days || 3)) : null)
      const nprBreakdown = result.breakdown_npr || {}

      const accom = result.breakdown?.accommodation ?? result.accommodation ?? null
      const foodVal = result.breakdown?.food ?? result.food ?? null
      const transportBase = result.breakdown?.transport ?? result.transport
      const localTransport = result.breakdown?.local_transport ?? result.local_transport
      const transVal = transportBase == null && localTransport == null ? null : Number(transportBase || 0) + Number(localTransport || 0)
      const actVal = result.breakdown?.activities ?? result.activities ?? null
      const shopVal = result.breakdown?.shopping ?? result.shopping ?? null
      const nprTransportBase = nprBreakdown.transport
      const nprLocalTransport = nprBreakdown.local_transport
      const nprTransVal = nprTransportBase == null && nprLocalTransport == null ? null : Number(nprTransportBase || 0) + Number(nprLocalTransport || 0)

      setEstimate({
        total: totalUsd,
        daily: dailyUsd,
        nprTotal: totalNpr,
        nprDaily: dailyNpr,
        source: result.baseline_source || result.source || "estimate",
        dataset: result.dataset || null,
        accommodation: accom,
        food: foodVal,
        transport: transVal,
        activities: actVal,
        shopping: shopVal,
        nprAccommodation: nprBreakdown.accommodation ?? null,
        nprFood: nprBreakdown.food ?? null,
        nprTransport: nprTransVal,
        nprActivities: nprBreakdown.activities ?? null,
        nprShopping: nprBreakdown.shopping ?? null,
        emergency_reserve: result.emergency_reserve_usd ?? result.emergency_reserve ?? null,
        nprEmergencyReserve: nprBreakdown.emergency_reserve ?? result.emergency_reserve_npr ?? null,
      })
    } catch (requestError) {
      if (requestError?.code === "ERR_CANCELED" || requestError?.name === "CanceledError" || requestError?.name === "AbortError") return
      if (requestId !== requestRef.current) return
      const message = requestError.response?.data?.detail || requestError.response?.data?.error || "We could not calculate an estimate right now. Please try again."
      setError(message)
      showToast(message, "error")
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false)
        if (abortRef.current === controller) abortRef.current = null
      }
    }
  }

  const onSubmit = (data) => {
    calculate(data)
  }

  const estimateValues = estimate
    ? currency === "NPR"
      ? {
          total: estimate.nprTotal,
          accommodation: estimate.nprAccommodation,
          food: estimate.nprFood,
          transport: estimate.nprTransport,
          activities: estimate.nprActivities,
          shopping: estimate.nprShopping,
          emergencyReserve: estimate.nprEmergencyReserve,
        }
      : currency === "USD"
        ? {
            total: estimate.total,
            accommodation: estimate.accommodation,
            food: estimate.food,
            transport: estimate.transport,
            activities: estimate.activities,
            shopping: estimate.shopping,
            emergencyReserve: estimate.emergency_reserve,
          }
        : { total: null, accommodation: null, food: null, transport: null, activities: null, shopping: null, emergencyReserve: null }
    : null
  const grandTotal = estimateValues?.total ?? null
  const emergencyReserve = estimateValues?.emergencyReserve ?? null

  return (
    <div className="ny-page container-app grid grid-cols-1 gap-8 py-6 sm:py-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <CMSPageIntro pageKey="budget-estimator" />
      {/* FORM */}
      <div>
        <PageHeader title="Budget Estimator" subtitle={<>Plan your Nepal trip expenses. The estimate updates automatically when
          you change your trip details.</>} icon={ FiDollarSign } />

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
                placeholder="Enter a destination"
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
            <p className="mt-2 text-xs leading-5 text-[var(--ny-text-muted)]">Currency values are shown only when the estimate service provides a verified conversion rate.</p>
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
        {error ? (
          <div role="alert" className="ny-panel p-6 text-center">
            <p className="font-bold text-[var(--ny-danger)]">Estimate unavailable</p>
            <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{error}</p>
            <button type="button" onClick={() => calculate(watched)} className="ny-btn ny-btn-secondary mt-4">Try again</button>
          </div>
        ) : estimate ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="card-base p-6 text-center bg-white border border-slate-200 shadow-md">
              <p className="text-sm text-gray-500">Estimated Total Cost</p>

              <p className="text-4xl font-extrabold text-saffron-600 my-1">
                {formatMoney(grandTotal, currency)}
              </p>

              <p className="text-xs text-gray-500">
                {currency === "USD" ? "USD estimate" : currency === "NPR" ? "NPR estimate" : "Selected currency conversion is not available from the verified estimate response"}
              </p>

              {estimate.source === "dataset_csv" ? (
                <p className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-green-800 bg-green-50 border border-green-200 px-3 py-1 rounded-full shadow-sm">
                  ✓ Based on real Nepal travel-cost dataset
                  {estimate.dataset
                    ? ` (${estimate.dataset.destinations}+ places)`
                    : ""}
                </p>
              ) : (
                <p className="mt-3 text-[11px] text-[var(--ny-text-secondary)]">Source returned by the estimate service: {estimate.source || "not specified"}. Treat this as planning guidance, not a quoted price.</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {CATEGORY_META.map(({ key, label, icon: Icon, color }) => (
                <div key={key} className="card-base p-4 flex items-center gap-3 bg-white border border-slate-200 shadow-sm">
                  <div className={`p-2.5 rounded-xl ${color}`}>
                    <Icon size={18} />
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="font-bold text-dark text-sm">
                      {formatMoney(estimateValues?.[key], currency)}
                    </p>
                  </div>
                </div>
              ))}

              <div className="card-base p-4 flex items-center gap-3 sm:col-span-2 lg:col-span-1 bg-slate-50 border border-slate-200">
                <div className="p-2.5 rounded-xl bg-amber-100 text-amber-800">
                  <FiShield size={18} />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Emergency reserve (if recorded)</p>
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
                "Activities & Sightseeing",
                "Shopping & Souvenirs",
              ]}
              data={[
                estimateValues?.accommodation,
                estimateValues?.food,
                estimateValues?.transport,
                estimateValues?.activities,
                estimateValues?.shopping,
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
