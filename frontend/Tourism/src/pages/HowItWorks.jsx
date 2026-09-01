import { useState } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiHelpCircle, FiMapPin, FiCompass, FiShield, FiDollarSign,
  FiBookOpen, FiUserCheck, FiCheckCircle, FiAlertCircle, FiInfo,
  FiSearch, FiDatabase, FiCpu, FiMessageSquare, FiSettings,
  FiLock, FiSliders, FiFileText, FiCalendar, FiArrowRight, FiChevronDown
} from "react-icons/fi"
import Breadcrumbs from "../components/common/Breadcrumbs"

export default function HowItWorks() {
  const [activeRole, setActiveRole] = useState("traveller") // 'traveller' or 'admin'
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedFaq, setExpandedFaq] = useState(null)

  const travellerTopics = [
    {
      id: "curation",
      title: "How Destinations are Curated & Verified",
      icon: <FiCompass className="text-purple-600 text-xl" />,
      content: `Our destination database is compiled from official Nepal Tourism Board registries, OpenStreetMap (OSM) spatial datasets, and verified local municipality archives across all 77 districts of Nepal. Places undergo strict data-cleaning pipelines before appearing live.`,
      highlights: [
        "Verified GPS coordinates from official cartographic surveys.",
        "Categorization across Heritage, Nature, Trekking, Religious, and Adventure.",
        "Administrative boundaries mapped down to Province, District, and Municipality."
      ]
    },
    {
      id: "honesty",
      title: "Map Pins & Unrecorded Data Policy",
      icon: <FiMapPin className="text-emerald-600 text-xl" />,
      titleBadge: "Strict Honesty Standard",
      content: `We enforce a strict Zero-Hallucination policy across the platform:`,
      highlights: [
        "Unmapped Places: Destinations lacking precise GPS coordinates do NOT get fake map pins placed in district centers. They are explicitly marked as 'Map location unavailable'.",
        "Missing Costs / Schedules: If food, lodging, or transport rates are unverified, we display 'Not recorded' rather than generating speculative prices.",
        "Opening Hours & Seasons: Unverified operational hours or best seasons are marked as 'Not recorded' to protect travelers from relying on invented information."
      ]
    },
    {
      id: "chatbot",
      title: "Himal AI Assistant Capabilities & Limits",
      icon: <FiMessageSquare className="text-blue-600 text-xl" />,
      content: `Himal AI is your intelligent Nepal travel companion grounded strictly on verified platform data.`,
      highlights: [
        "Grounding: Answers are derived from live destination profiles, emergency directories, and trained budget regressors.",
        "Honesty First: When asked about details missing from our database, Himal AI explicitly responds that the information is 'Not recorded' rather than guessing.",
        "Interactive Cards: Suggests real packages, trekking routes, and nearby police or hospital contacts."
      ]
    },
    {
      id: "reporting",
      title: "How to Report Incorrect Information",
      icon: <FiAlertCircle className="text-amber-600 text-xl" />,
      content: `Found outdated phone numbers, wrong coordinates, or changed entry fees? Travelers can actively contribute to platform quality.`,
      highlights: [
        "Submit Place / Edit Suggestion: Click 'Submit Place' or 'Suggest Correction' on any destination page.",
        "Review Process: Submissions are queued in the Admin Moderation Desk for field verification before publishing.",
        "Community Badges: Verified contributors earn community trust ratings."
      ]
    }
  ]

  const adminTopics = [
    {
      id: "overview",
      title: "Admin Dashboard Workspace Overview",
      icon: <FiSettings className="text-purple-600 text-xl" />,
      content: `The Admin Workspace provides total control over platform content, destination datasets, CMS blocks, and user feedback queues.`,
      highlights: [
        "Destinations Catalog: Search, filter, edit, or approve all 6,400+ destinations.",
        "Visitor Desk & Notices: Publish owner announcements, safety alerts, and seasonal notices.",
        "Festival & Event Calendar: Schedule local festivals with accurate dates and cultural guidelines.",
        "Data Quality & ML Sync: Manage destination JSON caches and feed updated data into prediction models."
      ]
    },
    {
      id: "editing",
      title: "Adding & Editing Destinations Safely",
      icon: <FiSliders className="text-emerald-600 text-xl" />,
      titleBadge: "Admin Best Practices",
      content: `When adding or updating destination records, strictly follow our content integrity principles:`,
      highlights: [
        "Coordinates Rule: Leave Latitude and Longitude blank if verified GPS coordinates are unavailable. The destination will safely present as 'Map location unavailable' without creating misleading map pins.",
        "Empty Fields: If opening hours, entry fees, or contact numbers are unknown, leave them empty. The system will cleanly display 'Not recorded'.",
        "City vs District: Do not copy district names into the 'City' field unless it is a recognized town/city center."
      ]
    },
    {
      id: "festivals",
      title: "Managing Visitor Notices & Festivals",
      icon: <FiCalendar className="text-blue-600 text-xl" />,
      content: `Promote local cultural events and emergency travel advisories across destination pages and landing banners.`,
      highlights: [
        "Visitor Notices: Add site alerts (e.g., trail maintenance, permit updates). Scheduled notices auto-expire.",
        "Festivals Catalog: Link local festivals to specific destinations, complete with dates, dress codes, and photography guidelines.",
        "Saved-Place Alerts: Publishing critical safety notices automatically notifies travelers who saved the destination."
      ]
    },
    {
      id: "moderation",
      title: "Content Moderation & Data Quality Rules",
      icon: <FiLock className="text-amber-600 text-xl" />,
      content: `Maintain platform security, copyright compliance, and data privacy.`,
      highlights: [
        "Media Licenses: Ensure uploaded destination covers and gallery photos carry Creative Commons or official rights.",
        "User Feedback & Approvals: Review tourist-submitted places and error reports from the Moderation Queue.",
        "Zero Fabrication Standard: Reject submissions containing speculative prices or unverified locations."
      ]
    }
  ]

  const faqs = [
    {
      q: "Why do some destinations say 'Map location unavailable'?",
      a: "Nepal's terrain includes remote alpine valleys and newly recognized heritage sites. If precise cartographic coordinates are not yet verified, we deliberately omit the map pin rather than showing a misleading fake location in the middle of a district center."
    },
    {
      q: "Why do some costs or operating hours say 'Not recorded'?",
      a: "Trekking permit fees, local lodge prices, and shrine opening hours can vary seasonally. To prevent travelers from relying on inaccurate or invented data, unverified fields display 'Not recorded' until confirmed by local authorities or site managers."
    },
    {
      q: "How does Himal AI handle questions about missing data?",
      a: "Himal AI is programmed never to hallucinate. If you ask about a price or schedule that is unrecorded in our dataset, it will openly tell you that the detail is not currently recorded."
    },
    {
      q: "How can an administrator add missing coordinates or details?",
      a: "Admins can log into the Admin Dashboard, navigate to the 'Destinations' tab, click 'Edit' on any record, fill in verified coordinates or operational details, and click 'Save Changes'. The updates instantly reflect across the platform."
    },
    {
      q: "Are emergency contacts and medical directory numbers verified?",
      a: "Yes. Emergency numbers (Tourist Police 1144, Nepal Police 100, Ambulance 102, and district hospital desks) are checked against official government emergency rosters across all 77 districts."
    }
  ]

  const activeTopics = activeRole === "traveller" ? travellerTopics : adminTopics

  const filteredTopics = activeTopics.filter((topic) =>
    topic.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    topic.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    topic.highlights.some(h => h.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "How This Works & Knowledge Base", to: "/how-it-works" }
      ]} />

      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 text-white p-8 sm:p-12 shadow-2xl border border-purple-800/30">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-300 text-xs font-semibold uppercase tracking-wider">
            <FiBookOpen size={14} /> Knowledge Base & System Transparency
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            How Nepal Tourism Platform Works
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Discover how we curate authentic destination data, uphold our strict Zero-Hallucination policy, and empower both travelers and administrators.
          </p>

          {/* Role Switcher Tabs */}
          <div className="pt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={() => setActiveRole("traveller")}
              className={`px-6 py-3 rounded-2xl font-bold text-xs sm:text-sm flex items-center gap-2.5 transition-all shadow-lg ${
                activeRole === "traveller"
                  ? "bg-purple-600 text-white shadow-purple-600/30 scale-105"
                  : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700"
              }`}
            >
              <FiUserCheck size={18} /> For Travellers & Visitors
            </button>

            <button
              onClick={() => setActiveRole("admin")}
              className={`px-6 py-3 rounded-2xl font-bold text-xs sm:text-sm flex items-center gap-2.5 transition-all shadow-lg ${
                activeRole === "admin"
                  ? "bg-amber-500 text-slate-950 shadow-amber-500/30 scale-105"
                  : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700"
              }`}
            >
              <FiSettings size={18} /> For Administrators & Staff
            </button>
          </div>
        </div>

        <div className="absolute -bottom-12 -right-12 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Search Bar & Role Info Callout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="md:col-span-2 relative">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${activeRole === "traveller" ? "traveller guide..." : "admin guidelines..."}`}
            className="w-full pl-11 pr-4 py-3.5 rounded-2xl bg-white border border-slate-200 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-purple-600 shadow-sm"
          />
        </div>

        <div className="p-3.5 rounded-2xl bg-purple-50 border border-purple-100 flex items-center gap-3 text-xs text-purple-900 font-medium">
          <FiInfo className="text-purple-600 shrink-0" size={20} />
          <span>
            {activeRole === "traveller"
              ? "Viewing Traveler Guide: Learn how data is verified and how map locations work."
              : "Viewing Admin Guide: Operating guidelines for destination editing and content rules."}
          </span>
        </div>
      </div>

      {/* Topics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredTopics.map((topic) => (
          <motion.div
            key={topic.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/80 hover:shadow-md transition-all flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-slate-100/80 border border-slate-200/60 inline-flex">
                  {topic.icon}
                </div>
                {topic.titleBadge && (
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                    {topic.titleBadge}
                  </span>
                )}
              </div>

              <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                {topic.title}
              </h3>

              <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
                {topic.content}
              </p>

              <div className="space-y-2 pt-2 border-t border-slate-100">
                {topic.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-700">
                    <FiCheckCircle className="text-emerald-500 shrink-0 mt-0.5" size={14} />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>

            {topic.id === "editing" && (
              <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-amber-900">
                  <FiAlertCircle /> Golden Rule for Admins
                </div>
                <p className="text-[11px] leading-snug">
                  Never fabricate coordinates or costs. Empty fields gracefully render as "Not recorded" or "Map location unavailable", which protects travelers.
                </p>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Honest Behavior Demonstration Matrix */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-900 text-xs font-bold uppercase tracking-wider">
              Data Integrity
            </span>
            <h2 className="text-2xl font-black text-slate-900 mt-1">
              Honest Data Behavior Standard
            </h2>
          </div>
          <p className="text-xs text-slate-500 max-w-md">
            Here is how our platform guarantees data honesty whenever verified details are missing from official datasets.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-900 uppercase font-bold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Field / Feature</th>
                <th className="py-3 px-4">When Data is Unverified</th>
                <th className="py-3 px-4">System Behavior</th>
                <th className="py-3 px-4">Admin Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-900">Destination GPS Coordinates</td>
                <td className="py-3 px-4 text-amber-700 font-medium">Latitude / Longitude Empty</td>
                <td className="py-3 px-4"><span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px]">Map location unavailable</span></td>
                <td className="py-3 px-4 text-slate-500">Edit destination & add verified GPS</td>
              </tr>
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-900">Estimated Travel Cost</td>
                <td className="py-3 px-4 text-amber-700 font-medium">No Budget Profile Recorded</td>
                <td className="py-3 px-4"><span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px]">Cost information unavailable</span></td>
                <td className="py-3 px-4 text-slate-500">Add budget profile in Admin Desk</td>
              </tr>
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-900">Best Time to Visit</td>
                <td className="py-3 px-4 text-amber-700 font-medium">Season Unrecorded</td>
                <td className="py-3 px-4"><span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px]">Not recorded</span></td>
                <td className="py-3 px-4 text-slate-500">Update seasonal details</td>
              </tr>
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-900">Opening Hours & Entry Fees</td>
                <td className="py-3 px-4 text-amber-700 font-medium">Hours / Fees Unrecorded</td>
                <td className="py-3 px-4"><span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px]">Not recorded</span></td>
                <td className="py-3 px-4 text-slate-500">Fill in visitor desk hours</td>
              </tr>
              <tr className="hover:bg-slate-50/50">
                <td className="py-3 px-4 font-bold text-slate-900">Festival & Event Notices</td>
                <td className="py-3 px-4 text-amber-700 font-medium">No Active Festival Scheduled</td>
                <td className="py-3 px-4"><span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px]">No active notices</span></td>
                <td className="py-3 px-4 text-slate-500">Publish notice via Visitor Desk</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Frequently Asked Questions */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200 space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
          <div className="p-3 rounded-2xl bg-purple-100 text-purple-700">
            <FiHelpCircle size={22} />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900">
              Frequently Asked Questions
            </h2>
            <p className="text-xs text-slate-500">Common questions from travelers and system administrators.</p>
          </div>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = expandedFaq === idx
            return (
              <div key={idx} className="border border-slate-200/80 rounded-2xl overflow-hidden transition-all">
                <button
                  onClick={() => setExpandedFaq(isOpen ? null : idx)}
                  className="w-full text-left p-4 bg-slate-50/60 hover:bg-slate-100/60 flex items-center justify-between font-bold text-slate-900 text-sm gap-4"
                >
                  <span>{faq.q}</span>
                  <FiChevronDown className={`shrink-0 text-slate-500 transition-transform ${isOpen ? "rotate-180 text-purple-600" : ""}`} size={18} />
                </button>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="p-4 bg-white text-xs sm:text-sm text-slate-600 leading-relaxed border-t border-slate-100"
                    >
                      {faq.a}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </div>

      {/* Quick Action Footer Callouts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-purple-900 to-slate-900 text-white rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl border border-purple-800/40">
          <span className="text-xs font-bold text-purple-300 uppercase tracking-wider">Ready to Explore?</span>
          <h3 className="text-2xl font-black">Discover Nepal's Heritage & Peaks</h3>
          <p className="text-slate-300 text-xs sm:text-sm">
            Browse verified destinations across all 7 provinces with live weather, maps, and safety advisories.
          </p>
          <Link
            to="/destinations"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-purple-600/30 transition-all"
          >
            Explore All Destinations <FiArrowRight />
          </Link>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-amber-950 text-white rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl border border-amber-800/40">
          <span className="text-xs font-bold text-amber-300 uppercase tracking-wider">Administrator Portal</span>
          <h3 className="text-2xl font-black">Manage Places & Visitor Desk</h3>
          <p className="text-slate-300 text-xs sm:text-sm">
            Add destinations, publish festival notices, manage user feedback, and maintain platform data quality.
          </p>
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-amber-500/30 transition-all"
          >
            Open Admin Dashboard <FiArrowRight />
          </Link>
        </div>
      </div>
    </div>
  )
}
