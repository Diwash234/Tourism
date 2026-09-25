import { Link } from "react-router-dom"
import { FiArrowLeft, FiShield } from "react-icons/fi"
import TourismLogo from "../branding/TourismLogo"

const PORTAL_THEMES = {
  tourist: { name: "Traveller portal", tagline: "Plan your journey across Nepal", hero: "/images/destinations/pokhara/fewatal.jpg", note: "Discover recorded places, shape an itinerary and keep practical travel information close.", role: "Traveller access" },
  staff: { name: "Staff operations", tagline: "Support Nepal's travel community", hero: "/images/destinations/gorkha/durbar.jpg", note: "A focused workspace for content, media, safety and guest support.", role: "Staff access" },
  admin: { name: "Administrator console", tagline: "Keep the platform trustworthy", hero: "/images/destinations/rani-mahal/palace.jpg", note: "Manage content, users, partners and safety information from one workspace.", role: "Administrator access" },
}

export default function AuthShell({ portal = "tourist", title, children, footer }) {
  const theme = PORTAL_THEMES[portal] || PORTAL_THEMES.tourist
  return (
    <div className="min-h-[100svh] bg-[var(--ny-bg)] lg:grid lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)]">
      <section className="relative hidden min-h-screen overflow-hidden bg-[var(--ny-green-deepest)] lg:block" aria-label="Nepal travel visual">
        <img src={theme.hero} alt="" className="absolute inset-0 h-full w-full object-cover opacity-65" />
        <div className="absolute inset-0 bg-[linear-gradient(145deg,rgba(4,42,36,0.94),rgba(4,42,36,0.48)_58%,rgba(4,42,36,0.82))]" />
        <div className="relative flex min-h-screen flex-col justify-between p-10 text-white xl:p-16">
          <Link to="/" className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-[#C7D9D2] hover:text-white"><FiArrowLeft size={16} aria-hidden="true" /> Back to Nepal Yatra</Link>
          <div className="max-w-xl"><span className="ny-kicker !border !border-[#63E6BE]/30 !bg-white/10 !text-[#BDEBD9]">{theme.role}</span><h1 className="mt-5 !text-4xl !text-white xl:!text-5xl">{theme.tagline}</h1><p className="mt-4 max-w-md text-base leading-7 text-[#C7D9D2]">{theme.note}</p><div className="mt-8 flex items-center gap-3 text-sm text-[#BDEBD9]"><span className="grid h-9 w-9 place-items-center rounded-full bg-white/10"><FiShield size={17} aria-hidden="true" /></span>Built for clear, practical decisions</div></div>
        </div>
      </section>
      <main className="flex min-h-screen items-center justify-center px-4 py-8 sm:px-6 lg:px-10">
        <div className="w-full max-w-md">
          <div className="mb-6 flex items-center justify-center lg:hidden"><Link to="/"><TourismLogo size="sm" /></Link></div>
          <div className="ny-panel p-6 sm:p-8"><p className="ny-kicker">{theme.name}</p><h1 className="mt-4 !text-2xl">{title}</h1><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{theme.tagline}</p><div className="mt-6">{children}</div></div>
          <div className="mt-5 text-center text-sm text-[var(--ny-text-secondary)]"><Link to="/" className="font-semibold text-[var(--ny-green)] hover:underline">← Return to the travel site</Link></div>
          {footer}
        </div>
      </main>
    </div>
  )
}
