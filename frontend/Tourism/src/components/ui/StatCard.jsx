export default function StatCard({
  icon: Icon,
  label,
  value,
  subtitle,
  accent = "blue",
  className = "",
}) {
  const ACCENTS = {
    blue: "bg-blue-50 text-blue-700 hover:border-blue-400",
    emerald: "bg-emerald-50 text-emerald-700 hover:border-emerald-400",
    amber: "bg-amber-50 text-amber-700 hover:border-amber-400",
    pink: "bg-pink-50 text-pink-700 hover:border-pink-400",
    purple: "bg-[#F7F8F5] text-[#102A2E] hover:border-purple-400",
  }

  const colorClass = ACCENTS[accent] || ACCENTS.blue

  return (
    <div
      className={`rounded-3xl bg-white border border-slate-200 p-5 shadow-sm transition-all hover:shadow-md ${colorClass} ${className}`}
    >
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-3 rounded-2xl bg-white/80 shadow-sm shrink-0">
            <Icon size={22} />
          </div>
        )}
        <div>
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-black text-slate-900 mt-0.5">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </div>
  )
}
