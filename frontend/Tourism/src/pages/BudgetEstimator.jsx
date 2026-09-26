import { useForm } from "react-hook-form"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiDollarSign, FiHome, FiCoffee, FiTruck, FiShield, FiFileText, FiLoader, FiExternalLink } from "react-icons/fi"

import budgetApi from "../api/budgetApi"
import travelApi from "../api/travelApi"
import PieChartCard from "../components/charts/PieChartCard"
import useToast from "../hooks/useToast"
import { DISPLAY_CURRENCIES, NATIONALITY_OPTIONS, formatCurrency, fromNpr, rateLabel } from "../utils/currency"

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

const CATEGORY_META = [
  { key: "accommodation", label: "Hotel & Lodging", icon: FiHome, color: "text-yellow-600 bg-yellow-50" },
  { key: "food", label: "Food & Dining", icon: FiCoffee, color: "text-orange-600 bg-orange-50" },
  { key: "transport", label: "Transport (incl. local)", icon: FiTruck, color: "text-blue-600 bg-blue-50" },
]

const BudgetEstimator = () => {
  const { register, handleSubmit, getValues, formState: { isSubmitting } } = useForm({
    defaultValues: { destination: "", travelers: 1, days: 3, style: "mid", nationality: "foreign", travel_month: "" },
  })

  const [estimate, setEstimate] = useState(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [rates, setRates] = useState(null)
  const [currency, setCurrency] = useState(() => {
    const saved = localStorage.getItem("tourism_currency")
    return saved && DISPLAY_CURRENCIES[saved] ? saved : "USD"
  })
  const { showToast } = useToast()
  const abortRef = useRef(null)

  useEffect(() => {
    let alive = true
    travelApi.fxRates()
      .then(({ data }) => { if (alive) setRates(data) })
      .catch(() => { if (alive) setRates({ available: false }) })
    return () => { alive = false; abortRef.current?.abort() }
  }, [])

  async function calculate(form) {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError("")
    try {
      const payload = {
        destination: form.destination,
        travelers: Number(form.travelers) || 1,
        days: Number(form.days) || 1,
        style: form.style,
        nationality: form.nationality,
        ...(form.travel_month ? { travel_month: Number(form.travel_month) } : {}),
      }
      const { data } = await budgetApi.estimate(payload, { signal: controller.signal })
      if (controller.signal.aborted) return
      setEstimate({ ...data, _days: payload.days, _travelers: payload.travelers })
    } catch (requestError) {
      if (requestError?.name === "CanceledError" || requestError?.code === "ERR_CANCELED") return
      const body = requestError.response?.data
      const message = body?.detail || body?.destination?.[0] || body?.error || "We could not calculate an estimate right now. Please try again."
      setError(typeof message === "string" ? message : "We could not calculate an estimate right now.")
      showToast(typeof message === "string" ? message : "Estimate failed", "error")
    } finally {
      if (abortRef.current === controller) setLoading(false)
    }
  }

  // Money helpers: NPR is the canonical currency (converted server-side at the
  // NRB rate). USD falls back to the service's own USD figures if NRB is down.
  const nrbAvailable = Boolean(rates?.available && estimate?.exchange_rate?.available)
  const show = (npr, usd = null) => {
    if (currency === "USD" && (npr == null || !nrbAvailable)) return formatCurrency(usd, "USD")
    if (currency === "NPR") return formatCurrency(npr, "NPR")
    return formatCurrency(fromNpr(npr, currency, rates), currency)
  }

  const bNpr = estimate?.breakdown_npr || {}
  const bUsd = estimate?.breakdown || {}
  const sum = (a, b) => (a == null && b == null ? null : Number(a || 0) + Number(b || 0))
  const categories = {
    accommodation: [bNpr.accommodation, bUsd.accommodation],
    food: [bNpr.food, bUsd.food],
    transport: [sum(bNpr.transport, bNpr.local_transport), sum(bUsd.transport, bUsd.local_transport)],
  }
  const fees = estimate?.official_fees
  const pieValue = (key) => {
    const [npr, usd] = categories[key]
    return currency === "USD" && !nrbAvailable ? usd : fromNpr(npr, currency, rates)
  }

  return (
    <div className="ny-page container-app grid grid-cols-1 gap-8 py-6 sm:py-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <CMSPageIntro pageKey="budget-estimator" />
      <div>
        <PageHeader title="Budget Estimator" subtitle={<>Living costs from the Nepal travel-cost dataset plus official visa, park, TIMS and permit fees. Converted with the Nepal Rastra Bank rate of the day.</>} icon={FiDollarSign} />

        <form onSubmit={(event) => handleSubmit(calculate)(event)} className="card-base p-6 space-y-4 shadow-md bg-white border border-slate-200" data-testid="budget-form">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label htmlFor="budget-destination" className="text-xs font-medium text-gray-500">Destination</label>
              <input id="budget-destination" className="input-field mt-1" placeholder="e.g. Upper Mustang, Namche Bazaar, Pokhara" {...register("destination", { required: true })} />
            </div>
            <div>
              <label htmlFor="budget-travelers" className="text-xs font-medium text-gray-500">Travelers</label>
              <input id="budget-travelers" type="number" min={1} max={20} className="input-field mt-1" {...register("travelers", { required: true })} />
            </div>
            <div>
              <label htmlFor="budget-days" className="text-xs font-medium text-gray-500">Duration (days)</label>
              <input id="budget-days" type="number" min={1} max={90} className="input-field mt-1" {...register("days", { required: true })} />
            </div>
            <div>
              <label htmlFor="budget-style" className="text-xs font-medium text-gray-500">Travel style</label>
              <select id="budget-style" className="input-field mt-1" {...register("style")}>
                <option value="budget">Budget</option>
                <option value="mid">Mid-range</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
            <div>
              <label htmlFor="budget-month" className="text-xs font-medium text-gray-500">Travel month (for seasonal permits)</label>
              <select id="budget-month" className="input-field mt-1" {...register("travel_month")}>
                <option value="">Not decided</option>
                {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="budget-nationality" className="text-xs font-medium text-gray-500">Nationality (official fees differ)</label>
              <select id="budget-nationality" className="input-field mt-1" {...register("nationality")}>
                {NATIONALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          <button type="submit" disabled={loading || isSubmitting} className="btn-primary w-full">
            {loading ? "Calculating…" : "Estimate budget"}
          </button>

          <div>
            <label htmlFor="budget-currency" className="text-xs font-medium text-gray-500">Display currency</label>
            <select id="budget-currency" className="input-field mt-1" value={currency}
              onChange={(e) => { setCurrency(e.target.value); localStorage.setItem("tourism_currency", e.target.value) }}>
              {Object.entries(DISPLAY_CURRENCIES).map(([code, c]) => (
                <option key={code} value={code}>{code} — {c.label} ({c.symbol})</option>
              ))}
            </select>
            <p className="mt-2 text-xs leading-5 text-[var(--ny-text-muted)]" data-testid="fx-rate-label">
              {rates ? rateLabel(rates) : "Loading official exchange rate…"}
              {rates?.source_url ? <> · <a className="underline" href="https://www.nrb.org.np/forex/" target="_blank" rel="noreferrer">NRB forex</a></> : null}
            </p>
          </div>

          {loading && (
            <p className="flex items-center gap-2 text-xs text-saffron-600"><FiLoader className="animate-spin" /> Calculating estimate…</p>
          )}
        </form>
      </div>

      <div>
        {error ? (
          <div role="alert" className="ny-panel p-6 text-center">
            <p className="font-bold text-[var(--ny-danger)]">Estimate unavailable</p>
            <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{error}</p>
            <button type="button" onClick={() => calculate(getValues())} className="ny-btn ny-btn-secondary mt-4">Try again</button>
          </div>
        ) : estimate ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6" data-testid="budget-result">
            <div className="card-base p-6 text-center bg-white border border-slate-200 shadow-md">
              {estimate.living_costs_available === false ? (
                <>
                  <p role="status" className="mb-3 rounded-xl border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900" data-testid="living-costs-unavailable">{estimate.living_costs_note}</p>
                  <p className="text-sm text-gray-500">Official permits & fees ({estimate._travelers} traveller{estimate._travelers > 1 ? "s" : ""})</p>
                  <p className="text-4xl font-extrabold text-saffron-600 my-1">{show(estimate.official_fees?.group_npr)}</p>
                </>
              ) : (
                <>
                  <p className="text-sm text-gray-500">Estimated trip total ({estimate._travelers} traveller{estimate._travelers > 1 ? "s" : ""}, {estimate._days} day{estimate._days > 1 ? "s" : ""})</p>
                  <p className="text-4xl font-extrabold text-saffron-600 my-1">{show(estimate.trip_total_npr, estimate.known_cost_total_usd)}</p>
                </>
              )}
              {estimate.living_costs_available !== false && <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                <p><span className="block text-xs text-gray-500">Per person</span><strong>{show(estimate.per_person_npr)}</strong></p>
                <p><span className="block text-xs text-gray-500">Per day (group)</span><strong>{show(estimate.per_day_npr)}</strong></p>
              </div>}
              {estimate.matched_destination && (
                <p className="mt-3 text-xs text-[var(--ny-text-secondary)]">
                  Estimated for <Link className="font-semibold underline" to={`/destinations/${estimate.matched_destination.id}`}>{estimate.matched_destination.name}</Link>
                  {estimate.matched_destination.district ? `, ${estimate.matched_destination.district}` : ""}
                </p>
              )}
              {estimate.living_costs_available !== false && <p className="mt-2 text-[11px] text-[var(--ny-text-secondary)]">
                {estimate.baseline_source === "dataset_csv" ? "Living costs: Nepal travel-cost dataset (USD ranges)." : `Living-cost source: ${estimate.baseline_source || "not specified"}.`}
                {" "}Activities, shopping and guide wages are not included (no recorded data). Planning guidance, not a quote.
              </p>}
            </div>

            {estimate.living_costs_available !== false && <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {CATEGORY_META.map(({ key, label, icon: Icon, color }) => (
                <div key={key} className="card-base p-4 flex items-center gap-3 bg-white border border-slate-200 shadow-sm">
                  <div className={`p-2.5 rounded-xl ${color}`}><Icon size={18} /></div>
                  <div>
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="font-bold text-dark text-sm">{show(categories[key][0], categories[key][1])}</p>
                  </div>
                </div>
              ))}
            </div>}

            <section className="card-base p-5 bg-white border border-slate-200" data-testid="official-fees" aria-labelledby="fees-heading">
              <h2 id="fees-heading" className="flex items-center gap-2 text-base font-bold"><FiFileText /> Official permits & fees</h2>
              {fees?.lines?.length ? (
                <ul className="mt-3 divide-y divide-slate-100 text-sm">
                  {fees.lines.map((line) => (
                    <li key={line.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 py-2">
                      <div className="min-w-0">
                        <p className="font-medium">{line.label}{line.estimate ? <span className="ml-1 text-xs text-amber-700">(estimate)</span> : null}</p>
                        {line.basis ? <p className="text-xs text-[var(--ny-text-muted)]">{line.basis}</p> : null}
                        {line.source?.url ? <a href={line.source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs underline">{line.source.publisher || "Source"} <FiExternalLink size={11} /></a> : null}
                      </div>
                      <p className="shrink-0 text-right font-semibold">
                        {line.amount_npr_per_person != null ? <>{show(line.amount_npr_per_person)}<span className="block text-xs font-normal text-gray-500">per person{line.currency === "USD" ? ` (US$${line.amount_per_person})` : ""}</span></> : <span className="text-xs font-normal text-gray-500">{line.note || "Set by agency — not quoted"}</span>}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">No official entry fee or permit is recorded for this destination and nationality.</p>
              )}
              {fees?.lines?.length ? (
                <p className="mt-2 flex justify-between border-t border-slate-200 pt-2 text-sm font-bold">
                  <span>Official fees (group)</span><span>{show(fees.group_npr)}</span>
                </p>
              ) : null}
              {fees?.matching_note ? <p className="mt-2 text-xs text-[var(--ny-text-muted)]">{fees.matching_note}</p> : null}
              <p className="mt-2 text-xs"><Link className="underline" to="/before-you-travel">Full visa, TIMS, permit & insurance guide →</Link></p>
            </section>

            {estimate.contingency_suggested_npr != null && <div className="card-base p-4 flex items-center gap-3 bg-slate-50 border border-slate-200">
              <div className="p-2.5 rounded-xl bg-amber-100 text-amber-800"><FiShield size={18} /></div>
              <div>
                <p className="text-xs text-gray-500 font-medium">Suggested contingency buffer (10%)</p>
                <p className="font-bold text-dark text-sm">{show(estimate.contingency_suggested_npr)}</p>
                <p className="text-[11px] text-[var(--ny-text-muted)]">{estimate.contingency_note}</p>
              </div>
            </div>}

            {estimate.living_costs_available !== false && <PieChartCard title="Living-cost breakdown" labels={CATEGORY_META.map((c) => c.label)} data={CATEGORY_META.map((c) => pieValue(c.key))} />}
          </motion.div>
        ) : (
          <div className="card-base p-10 text-center text-gray-400 h-full flex items-center justify-center bg-white border border-slate-200">
            Enter your trip details and press “Estimate budget”.
          </div>
        )}
      </div>
    </div>
  )
}

export default BudgetEstimator
