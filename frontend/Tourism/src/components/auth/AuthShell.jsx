import { Link } from "react-router-dom"
import TourismLogo from "../branding/TourismLogo"

/**
 * AuthShell
 * Shared layout for all login / register pages. The `portal` prop changes
 * the colour identity and copy so the User, Staff and Admin portals are
 * visually distinct instead of looking like one identical AI-generated form.
 *
 *  - tourist  -> teal/forest (travel, adventure)
 *  - staff    -> saffron/amber (operations desk)
 *  - admin    -> deep slate/red (control + security)
 */
const PORTAL_THEMES = {
  tourist: {
    name: "Traveller Portal",
    tagline: "Plan your journey across Nepal",
    accent: "from-teal-600 to-emerald-600",
    ring: "ring-teal-400",
    badge: "bg-teal-50 text-teal-700 border-teal-200",
    hero: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1400&q=80",
    note: "Explore 6,000+ destinations, build itineraries and estimate trip costs.",
  },
  staff: {
    name: "Staff Operations Desk",
    tagline: "Moderation, approvals & guest support",
    accent: "from-amber-500 to-orange-600",
    ring: "ring-amber-400",
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    hero: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1400&q=80",
    note: "Staff accounts are issued by an administrator. Contact your supervisor for access.",
  },
  admin: {
    name: "Administrator Console",
    tagline: "Full platform control & RBAC",
    accent: "from-slate-800 to-nepalred-600",
    ring: "ring-nepalred-400",
    badge: "bg-slate-100 text-slate-700 border-slate-300",
    hero: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1400&q=80",
    note: "Super-admin accounts are created securely on the server with `python manage.py createsuperuser`.",
  },
}

export default function AuthShell({
  portal = "tourist",
  title,
  children,
  footer,
}) {
  const t = PORTAL_THEMES[portal] || PORTAL_THEMES.tourist

  return (
    <div className="min-h-[88vh] grid lg:grid-cols-2">
      {/* Visual side */}
      <div className="relative hidden lg:block overflow-hidden">
        <img
          src={t.hero}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-black/40 to-black/70" />
        <div className="relative z-10 h-full flex flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <TourismLogo size="sm" />
            <span className="font-bold tracking-wide">Digital Nepal Tourism</span>
          </div>
          <div>
            <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full border ${t.badge}`}>
              {t.name}
            </span>
            <h2 className="mt-4 text-4xl font-black leading-tight">{t.tagline}</h2>
            <p className="mt-3 text-white/80 max-w-md">{t.note}</p>
          </div>
        </div>
      </div>

      {/* Form side */}
      <div className="flex items-center justify-center px-4 py-12 bg-gray-50">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-center gap-2 mb-6 lg:hidden">
            <TourismLogo size="sm" />
          </div>

          <div className={`bg-white rounded-2xl shadow-xl border border-gray-100 p-8 ring-1 ${t.ring}/10`}>
            <h1 className="text-2xl font-black text-gray-900">{title}</h1>
            <p className="text-sm text-gray-500 mt-1 mb-6">{t.tagline}</p>
            {children}
          </div>

          <div className="text-center text-xs text-gray-400 mt-6">
            <Link to="/" className="hover:text-gray-600">← Back to home</Link>
          </div>
          {footer}
        </div>
      </div>
    </div>
  )
}
