import { Link } from "react-router-dom"

const TONE = {
  festival: "border-amber-200 bg-amber-50 text-amber-950",
  closure: "border-rose-200 bg-rose-50 text-rose-950",
  permit: "border-sky-200 bg-sky-50 text-sky-950",
  seasonal: "border-emerald-200 bg-emerald-50 text-emerald-950",
  crowd: "border-orange-200 bg-orange-50 text-orange-950",
  transport: "border-indigo-200 bg-indigo-50 text-indigo-950",
  info: "border-slate-200 bg-slate-50 text-slate-900",
}

const LABEL = {
  festival: "Festival",
  closure: "Closure",
  permit: "Permit",
  seasonal: "Seasonal",
  crowd: "Crowds",
  transport: "Transport",
  info: "Notice",
}

export default function VisitorNoticeBanner({ notices = [] }) {
  if (!notices.length) return null
  return (
    <section className="space-y-3" aria-label="Visitor notices">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-black uppercase tracking-wider text-emerald-800">From the tourism desk</p>
          <h2 className="text-lg font-bold text-slate-900">Before you go</h2>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {notices.slice(0, 6).map((notice) => {
          const card = (
            <article className={`rounded-2xl border p-4 ${TONE[notice.kind] || TONE.info}`}>
              <p className="text-[10px] font-black uppercase tracking-wider">{LABEL[notice.kind] || "Notice"}</p>
              <h3 className="font-bold mt-1">{notice.title}</h3>
              {notice.body && <p className="text-sm mt-1 leading-relaxed">{notice.body}</p>}
              {(notice.destination_name || notice.city || notice.district) && (
                <p className="text-xs mt-2 opacity-80">
                  {[notice.destination_name, notice.city, notice.district].filter(Boolean).join(" · ")}
                </p>
              )}
            </article>
          )
          if (notice.destination_slug) {
            return (
              <Link key={notice.id} to={`/destinations/${notice.destination_slug}`} className="block hover:opacity-95">
                {card}
              </Link>
            )
          }
          return <div key={notice.id}>{card}</div>
        })}
      </div>
    </section>
  )
}
