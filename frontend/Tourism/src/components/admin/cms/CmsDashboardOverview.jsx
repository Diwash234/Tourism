import { FiLayers, FiFileText, FiActivity, FiCheckCircle, FiExternalLink, FiCompass, FiShield, FiMessageSquare, FiTrendingUp } from "react-icons/fi"
import { BsHouseDoor, BsBorderTop, BsLayoutTextWindow, BsLayoutThreeColumns, BsMegaphone, BsChatDots, BsNewspaper, BsExclamationCircle } from "react-icons/bs"

export default function CmsDashboardOverview({
  totalPages = 65,
  totalSections = 150,
  contentCounts = {},
  onNavigate,
}) {
  const quickActions = [
    { title: "Home Page & Hero", desc: "Hero slides, featured editorial, live packages", icon: BsHouseDoor, action: () => onNavigate("page", "home") },
    { title: "Topbar & 1144 Helpline", desc: "24/7 Tourist Police, live weather ticker", icon: BsBorderTop, action: () => onNavigate("global_section", "topbar") },
    { title: "Live Marquee Tickers", desc: "Breaking route status, passes & advisories", icon: FiTrendingUp, action: () => onNavigate("global_section", "tickers") },
    { title: "Himal AI Assistant", desc: "Greeting messages, prompts, brand theme", icon: BsChatDots, action: () => onNavigate("global_section", "chat_widget") },
    { title: "Official Travel Notices", desc: "19 safety advisories and route bulletins", icon: BsExclamationCircle, action: () => onNavigate("content", "notices") },
    { title: "Global CTA Banners", desc: "Autumn season promotions & expedition CTAs", icon: BsMegaphone, action: () => onNavigate("global_section", "cta_banners") },
  ]

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#0B132B] via-[#0E1E38] to-[#0A1128] p-6 sm:p-8 text-white shadow-xl border border-slate-800">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/20 px-3 py-1 text-xs font-semibold text-blue-300 border border-blue-500/30 mb-3">
            <FiActivity className="text-emerald-400" />
            <span>Public Website CMS Pipeline Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            CMS Admin Control Center
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-slate-300 leading-relaxed">
            Manage all 65 public pages, global headers, footers, tickers, and content collections. Changes published here immediately reflect across the public traveller website.
          </p>
        </div>

        {/* Decorative background element */}
        <div className="pointer-events-none absolute -right-10 -bottom-10 h-48 w-48 rounded-full bg-blue-600/10 blur-2xl" />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Total Managed Pages</span>
          <p className="text-2xl font-black text-slate-900 dark:text-white mt-1">{totalPages}</p>
          <span className="text-[11px] text-emerald-600 font-semibold">● 100% Route Coverage</span>
        </div>

        <div className="bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Content Sections</span>
          <p className="text-2xl font-black text-slate-900 dark:text-white mt-1">{totalSections}+</p>
          <span className="text-[11px] text-emerald-600 font-semibold">● Snapshot Isolated</span>
        </div>

        <div className="bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Global Sections</span>
          <p className="text-2xl font-black text-slate-900 dark:text-white mt-1">8</p>
          <span className="text-[11px] text-blue-600 font-semibold">Navbar, Topbar, Tickers</span>
        </div>

        <div className="bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Active Notices</span>
          <p className="text-2xl font-black text-slate-900 dark:text-white mt-1">{contentCounts.notices || 19}</p>
          <span className="text-[11px] text-amber-600 font-semibold">National Safety Advisories</span>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3">
          Quick Launch Section Editors
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {quickActions.map((qa, idx) => {
            const Icon = qa.icon
            return (
              <button
                key={idx}
                type="button"
                onClick={qa.action}
                className="group p-4 rounded-xl bg-white dark:bg-[#0E1E1B] border border-slate-200 dark:border-emerald-900/40 text-left shadow-sm hover:border-blue-500 hover:shadow-md transition-all flex items-start gap-3"
              >
                <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  <Icon size={18} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {qa.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                    {qa.desc}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* System Integrity Info */}
      <div className="rounded-xl bg-slate-50 dark:bg-slate-900/80 p-4 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
          <FiCheckCircle className="text-emerald-500 shrink-0" size={15} />
          <span>
            <b>Live Publishing Pipeline:</b> When you click <i>Publish to Website</i>, frozen snapshots synchronize immediately and clear client cache across all tabs.
          </span>
        </div>

        <a
          href="/"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 font-bold hover:underline shrink-0"
        >
          <span>Open Public Website</span>
          <FiExternalLink size={12} />
        </a>
      </div>
    </div>
  )
}
