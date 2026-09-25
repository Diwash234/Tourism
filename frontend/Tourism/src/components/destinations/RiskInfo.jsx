import { FiShield, FiAlertTriangle } from "react-icons/fi"

export default function RiskInfo({ riskAnalysis, alertTitle }) {
  const score = riskAnalysis?.tourism_risk_index ?? null
  const category = riskAnalysis?.risk_category ? String(riskAnalysis.risk_category).toUpperCase() : null
  const color = category === "LOW" ? "bg-emerald-100 text-emerald-800" : category === "MODERATE" ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800"

  return (
    <section className="ny-card space-y-4 p-5" aria-labelledby="risk-info-title">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--ny-border)] pb-3">
        <h2 id="risk-info-title" className="flex items-center gap-2 text-base font-bold"><FiShield className="text-[var(--ny-green)]" aria-hidden="true" /> Safety & risk information</h2>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${score == null ? "bg-slate-100 text-slate-600" : color}`}>{category ? `${category} risk` : "Unavailable"}</span>
      </div>
      <div className="space-y-2 text-sm text-[var(--ny-text-secondary)]">
        <div className="flex justify-between gap-3"><span>Tourism risk index:</span><b className="text-[var(--ny-text)]">{score == null ? "Not available" : `${score} / 100`}</b></div>
        <div className="flex justify-between gap-3"><span>Natural hazard level:</span><b className={score == null ? "text-[var(--ny-text)]" : score < 40 ? "text-[var(--ny-success)]" : "text-[var(--ny-warning)]"}>{score == null ? "Not available" : score < 40 ? "Lower advisory level" : "Advisory active"}</b></div>
      </div>
      <p className="flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-gold)] p-3 text-xs text-[var(--ny-text-secondary)]"><FiAlertTriangle size={15} className="mt-0.5 shrink-0 text-[var(--ny-warning)]" aria-hidden="true" />{alertTitle || "No alert record was supplied for this destination. Check current local and official sources before travelling."}</p>
    </section>
  )
}
