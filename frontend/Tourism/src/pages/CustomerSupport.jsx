import { useState } from "react"
import { FiHeadphones, FiMessageSquare, FiSend, FiCheckCircle, FiPhoneCall, FiMail, FiHelpCircle } from "react-icons/fi"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"
import UserFeedbackModal from "../components/user/UserFeedbackModal"

export default function CustomerSupport() {
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)

  return (
    <ResponsiveContainer className="py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "Customer Support & Admin Help Desk", to: "/support" }
      ]} />

      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 text-white p-8 sm:p-12 shadow-2xl border border-purple-800/30">
        <div className="relative z-10 max-w-3xl space-y-4">
          <span className="px-3.5 py-1 rounded-full bg-amber-400/20 text-amber-300 text-xs font-bold uppercase tracking-wider border border-amber-400/30">
            24/7 Traveler Help Desk
          </span>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Customer Support & Admin Help Desk
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Have questions about your trip, itinerary calculations, or destination details? Contact our support team or chat with Himal AI.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-3">
          <div className="p-3 rounded-2xl bg-purple-100 text-purple-700 w-fit">
            <FiMessageSquare size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Direct Admin Feedback & Support</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Submit inquiries, bug reports, or rating feedback directly to the Admin Support Desk.
          </p>
          <button
            onClick={() => setShowFeedbackModal(true)}
            className="w-full py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs shadow"
          >
            Open Support & Feedback Form
          </button>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-3">
          <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-700 w-fit">
            <FiHeadphones size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Himal AI Assistant</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Chat 24/7 with Himal AI for instant dataset-grounded travel advice and emergency helplines.
          </p>
          <a
            href="/chatbot"
            className="block text-center w-full py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow"
          >
            Launch Himal AI Assistant
          </a>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-3">
          <div className="p-3 rounded-2xl bg-amber-100 text-amber-700 w-fit">
            <FiPhoneCall size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Emergency Helplines</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Access 24/7 Tourist Police (1144), Nepal Police (100), Ambulance (102), and hospital rosters.
          </p>
          <a
            href="/emergency"
            className="block text-center w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow"
          >
            Open Emergency Directory
          </a>
        </div>
      </div>

      <UserFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
    </ResponsiveContainer>
  )
}
