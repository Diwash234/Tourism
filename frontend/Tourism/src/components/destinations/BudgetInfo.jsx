import { FiDollarSign } from "react-icons/fi"

const money = (value, currency = "USD") => value == null ? "Not recorded" : `${currency} ${Number(value).toLocaleString()}`

export default function BudgetInfo({ budgetEst, entryFee = null }) {
  const dailyCost = budgetEst?.estimated_daily_budget ?? null
  const totalCost = budgetEst?.estimated_trip_budget ?? null
  const currency = budgetEst?.currency || "USD"

  return (
    <section className="ny-card space-y-4 p-5" aria-labelledby="budget-breakdown-title">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--ny-border)] pb-3">
        <h2 id="budget-breakdown-title" className="flex items-center gap-2 text-base font-bold"><FiDollarSign className="text-[var(--ny-green)]" aria-hidden="true" /> Travel budget information</h2>
        <span className="rounded-full bg-[var(--ny-soft-green)] px-2.5 py-1 text-[10px] font-bold uppercase text-[var(--ny-green)]">Recorded estimate</span>
      </div>
      <div><p className="text-xs text-[var(--ny-text-secondary)]">Estimated daily budget</p><p className="mt-1 text-3xl font-bold text-[var(--ny-text)]">{money(dailyCost, currency)} {dailyCost != null && <span className="text-xs font-semibold text-[var(--ny-text-secondary)]">/ day</span>}</p></div>
      <div className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-white p-3.5 text-sm text-[var(--ny-text-secondary)]"><div className="flex justify-between gap-3"><span>Estimated trip total</span><b className="text-[var(--ny-text)]">{money(totalCost, currency)}</b></div><div className="mt-2 flex justify-between gap-3"><span>Accommodation / night</span><b className="text-[var(--ny-text)]">{money(budgetEst?.accommodation_per_night, currency)}</b></div><div className="mt-2 flex justify-between gap-3"><span>Food / day</span><b className="text-[var(--ny-text)]">{money(budgetEst?.food_cost_per_day, currency)}</b></div><div className="mt-2 flex justify-between gap-3"><span>Transport</span><b className="text-[var(--ny-text)]">{money(budgetEst?.transport_cost, currency)}</b></div><div className="mt-2 flex justify-between gap-3"><span>Entry fee</span><b className="text-[var(--ny-text)]">{entryFee == null ? "Not recorded" : `NPR ${Number(entryFee).toLocaleString()}`}</b></div></div>
      <p className="text-xs leading-5 text-[var(--ny-text-secondary)]">These values are estimates only when supplied by the destination record. Confirm current prices, availability and currency with the relevant provider.</p>
    </section>
  )
}
