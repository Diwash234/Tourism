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
import destinationApi from "../api/destinationApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"
import { useI18n } from "../i18n"
import { DISPLAY_CURRENCIES, formatCurrency, fromNpr, nprPerUnit, rateLabel } from "../utils/currency"

const CATEGORY_META = [
  {
    key: "accommodation",
    labelKey: "budgetest.cat_hotel",
    fallback: "Hotel & Lodging",
    icon: FiHome,
    color: "text-yellow-600 bg-yellow-50",
  },
  {
    key: "food",
    labelKey: "budgetest.cat_food",
    fallback: "Food & Dining",
    icon: FiCoffee,
    color: "text-orange-600 bg-orange-50",
  },
  {
    key: "transport",
    labelKey: "budgetest.cat_transport",
    fallback: "Transport & Transit",
    icon: FiTruck,
    color: "text-blue-600 bg-blue-50",
  },
  {
    key: "activities",
    labelKey: "budgetest.cat_activities",
    fallback: "Sightseeing & Activities",
    icon: FiCompass,
    color: "text-emerald-700 bg-[#F7F8F5]",
  },
  {
    key: "shopping",
    labelKey: "budgetest.cat_shopping",
    fallback: "Local Shopping & Souvenirs",
    icon: FiShoppingBag,
    color: "text-emerald-600 bg-emerald-50",
  },
]

const BudgetEstimator = () => {
  const { t } = useI18n()
  const {
    register,
    handleSubmit,
    control,
    setValue,
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
  const [exchangeRates, setExchangeRates] = useState(null)
  const [destinationSuggestions, setDestinationSuggestions] = useState([])
  const [selectedDestination, setSelectedDestination] = useState(null)
  const [searchingDestinations, setSearchingDestinations] = useState(false)
  const { showToast } = useToast()
  const debounceRef = useRef(null)
  const requestRef = useRef(0)
  const abortRef = useRef(null)
  const destinationSearchRef = useRef(0)

  const watched = useWatch({ control })

  useEffect(() => {
    let active = true
    budgetApi.getExchangeRates()
      .then(({ data }) => { if (active) setExchangeRates(data) })
      .catch((rateError) => {
        if (active) setExchangeRates(rateError?.response?.data || { available: false })
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    const query = String(watched?.destination || "").trim()
    const requestId = ++destinationSearchRef.current
    if (selectedDestination?.name?.toLowerCase() === query.toLowerCase() || query.length < 2) {
      const clearTimer = setTimeout(() => {
        setDestinationSuggestions([])
        setSearchingDestinations(false)
      }, 0)
      return () => clearTimeout(clearTimer)
    }

    const timer = setTimeout(async () => {
      setSearchingDestinations(true)
      try {
        const { data } = await destinationApi.autocomplete(query, { limit: 8, type: "attraction" })
        if (requestId === destinationSearchRef.current) {
          const rows = Array.isArray(data) ? data : data?.results || data?.data || []
          setDestinationSuggestions(rows)
        }
      } catch {
        if (requestId === destinationSearchRef.current) setDestinationSuggestions([])
      } finally {
        if (requestId === destinationSearchRef.current) setSearchingDestinations(false)
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [watched?.destination, selectedDestination])

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
      const selectedName = selectedDestination?.name?.toLowerCase()
      const inputName = String(data.destination || "").trim().toLowerCase()
      const requestData = selectedName && selectedName === inputName
        ? { ...data, destination: selectedDestination.id }
        : data
      const { data: result } = await budgetApi.estimate(requestData, { signal: controller.signal })

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
        nprTotal: result.trip_total_npr ?? totalNpr,
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

  const convertBudgetAmount = (usdAmount, nprAmount) => {
    if (currency === "NPR") {
      if (nprAmount != null) return nprAmount
      const usdRate = nprPerUnit(exchangeRates, "USD")
      return usdAmount != null && usdRate != null ? Number(usdAmount) * usdRate : null
    }
    if (nprAmount != null) return fromNpr(nprAmount, currency, exchangeRates)
    const usdRate = nprPerUnit(exchangeRates, "USD")
    const amountNpr = usdAmount != null && usdRate != null ? Number(usdAmount) * usdRate : null
    return amountNpr == null ? (currency === "USD" ? usdAmount : null) : fromNpr(amountNpr, currency, exchangeRates)
  }

  const estimateValues = estimate
    ? {
        total: convertBudgetAmount(estimate.total, estimate.nprTotal),
        accommodation: convertBudgetAmount(estimate.accommodation, estimate.nprAccommodation),
        food: convertBudgetAmount(estimate.food, estimate.nprFood),
        transport: convertBudgetAmount(estimate.transport, estimate.nprTransport),
        activities: convertBudgetAmount(estimate.activities, estimate.nprActivities),
        shopping: convertBudgetAmount(estimate.shopping, estimate.nprShopping),
        emergencyReserve: convertBudgetAmount(estimate.emergency_reserve, estimate.nprEmergencyReserve),
      }
    : null
  const grandTotal = estimateValues?.total ?? null
  const emergencyReserve = estimateValues?.emergencyReserve ?? null

  return (
    <div className="ny-page container-app grid grid-cols-1 gap-8 py-6 sm:py-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <CMSPageIntro pageKey="budget-estimator" />
      {/* FORM */}
      <div>
        <PageHeader title={t("budgetest.title")} subtitle={t("budgetest.subtitle")} icon={ FiDollarSign } />

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="card-base p-6 space-y-4 shadow-md bg-white border border-slate-200"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">
                {t("budgetest.destination")}
              </label>
              <input
                className="input-field mt-1"
                placeholder={t("budgetest.destination_ph")}
                autoComplete="off"
                {...register("destination", {
                  required: true,
                  onChange: (event) => {
                    if (event.target.value.trim().toLowerCase() !== selectedDestination?.name?.toLowerCase()) {
                      setSelectedDestination(null)
                    }
                  },
                })}
              />
              {destinationSuggestions.length > 0 && (
                <ul className="mt-1 max-h-52 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg" role="listbox" aria-label="Destination matches">
                  {destinationSuggestions.map((place) => (
                    <li key={place.id || place.slug}>
                      <button
                        type="button"
                        role="option"
                        aria-selected="false"
                        className="w-full px-3 py-2 text-left text-sm hover:bg-emerald-50"
                        onClick={() => {
                          setSelectedDestination(place)
                          setValue("destination", place.name, { shouldDirty: true, shouldValidate: true })
                          setDestinationSuggestions([])
                        }}
                      >
                        <span className="block font-semibold text-slate-800">{place.name}</span>
                        <span className="block text-xs text-slate-500">{[place.district, place.province].filter(Boolean).join(", ")}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {searchingDestinations && <p className="mt-1 text-xs text-slate-500">Searching the destination catalogue…</p>}
              {selectedDestination && <p className="mt-1 text-xs font-medium text-emerald-700">Matched to catalogue: {selectedDestination.name}</p>}
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500">
                {t("budgetest.travelers")}
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
                {t("budgetest.duration")}
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
                {t("budgetest.style")}
              </label>
              <select className="input-field mt-1" {...register("style")}>
                <option value="budget">{t("budgetest.style_budget")}</option>
                <option value="mid">{t("budgetest.style_mid")}</option>
                <option value="luxury">{t("budgetest.style_luxury")}</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || isSubmitting}
            className="btn-primary w-full"
          >
            {loading || isSubmitting ? t("budgetest.calculating") : t("budgetest.estimate_cta")}
          </button>

          <div className="mt-4">
            <label className="text-xs font-medium text-gray-500">
              {t("budgetest.display_currency")}
            </label>
            <select
              className="input-field mt-1"
              value={currency}
              onChange={(e) => {
                setCurrency(e.target.value)
                localStorage.setItem("tourism_currency", e.target.value)
              }}
            >
              {Object.entries(DISPLAY_CURRENCIES).map(([code, c]) => (
                <option key={code} value={code}>
                  {code} — {c.label} ({c.symbol})
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs leading-5 text-[var(--ny-text-muted)]">{t("budgetest.currency_note")}</p>
            {exchangeRates && <p className="mt-1 text-xs leading-5 text-[var(--ny-text-muted)]">{rateLabel(exchangeRates)}</p>}
          </div>

          {loading && (
            <p className="flex items-center gap-2 text-xs text-saffron-600">
              <FiLoader className="animate-spin" />
              {t("budgetest.updating")}
            </p>
          )}
        </form>
      </div>

      {/* RESULT */}
      <div>
        {error ? (
          <div role="alert" className="ny-panel p-6 text-center">
            <p className="font-bold text-[var(--ny-danger)]">{t("budgetest.unavailable_title")}</p>
            <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{error}</p>
            <button type="button" onClick={() => calculate(watched)} className="ny-btn ny-btn-secondary mt-4">{t("common.try_again")}</button>
          </div>
        ) : estimate ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="card-base p-6 text-center bg-white border border-slate-200 shadow-md">
              <p className="text-sm text-gray-500">{t("budgetest.total")}</p>

              <p className="text-4xl font-extrabold text-saffron-600 my-1">
                {formatCurrency(grandTotal, currency)}
              </p>

              <p className="text-xs text-gray-500">
                {currency === "USD" ? t("budgetest.usd_note") : currency === "NPR" ? t("budgetest.npr_note") : t("budgetest.fx_unavailable")}
              </p>

              {estimate.source === "dataset_csv" ? (
                <p className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-green-800 bg-green-50 border border-green-200 px-3 py-1 rounded-full shadow-sm">
                  {t("budgetest.dataset_badge")}
                  {estimate.dataset
                    ? ` (${estimate.dataset.destinations}+ ${t("budgetest.places_unit")})`
                    : ""}
                </p>
              ) : (
                <p className="mt-3 text-[11px] text-[var(--ny-text-secondary)]">{t("budgetest.source_note", { source: estimate.source || t("budgetest.not_specified") })}</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {CATEGORY_META.map(({ key, labelKey, fallback, icon: Icon, color }) => (
                <div key={key} className="card-base p-4 flex items-center gap-3 bg-white border border-slate-200 shadow-sm">
                  <div className={`p-2.5 rounded-xl ${color}`}>
                    <Icon size={18} />
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">{t(labelKey) !== labelKey ? t(labelKey) : fallback}</p>
                    <p className="font-bold text-dark text-sm">
                      {formatCurrency(estimateValues?.[key], currency)}
                    </p>
                  </div>
                </div>
              ))}

              <div className="card-base p-4 flex items-center gap-3 sm:col-span-2 lg:col-span-1 bg-slate-50 border border-slate-200">
                <div className="p-2.5 rounded-xl bg-amber-100 text-amber-800">
                  <FiShield size={18} />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">{t("budgetest.emergency_reserve")}</p>
                  <p className="font-bold text-dark text-sm">
                    {formatCurrency(emergencyReserve, currency)}
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
