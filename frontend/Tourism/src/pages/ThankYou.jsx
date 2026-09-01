import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import { FiCheckCircle, FiCompass, FiPhoneCall, FiArrowRight, FiShield } from "react-icons/fi"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { FadeIn, HoverCard } from "../components/common/MotionSystem"

export default function ThankYou() {
  return (
    <div className="container-app py-12 max-w-3xl animate-fadeIn">
      <Breadcrumbs items={[{ label: "Submission Confirmed", to: "/thank-you" }]} />

      <FadeIn className="text-center space-y-6 card-base p-8 sm:p-12 rounded-3xl shadow-2xl border border-purple-100 bg-white">
        <div className="w-20 h-20 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center shadow-lg shadow-emerald-500/10">
          <FiCheckCircle size={44} />
        </div>

        <div>
          <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-bold uppercase tracking-wider">
            Submission Received
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-3">
            Dhanyabad! Your Submission is in Good Hands 🙏
          </h1>
          <p className="text-gray-600 text-sm max-w-lg mx-auto mt-2 leading-relaxed">
            Thank you for contributing to the Nepal Tourism portal. Your submission has been securely queued in the Admin Moderation & Verification Sentinel.
          </p>
        </div>

        {/* Truthful Response-Time Promise */}
        <div className="p-4 rounded-2xl bg-purple-50/80 border border-purple-200 text-xs text-purple-900 flex items-center justify-center gap-2 max-w-md mx-auto">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span><b>Response Promise:</b> Moderation team reviews within <b>2 hours</b> · 24/7 Helpline: <b>1144</b></span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left pt-4">
          <HoverCard className="p-4 rounded-2xl border border-purple-100 bg-gradient-to-br from-white to-purple-50">
            <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1.5">
              <FiCompass className="text-purple-700" /> Explore Destinations
            </h4>
            <p className="text-xs text-gray-500 mt-1">Browse recorded destinations across Nepal. Empty fields stay Not recorded.</p>
            <Link to="/destinations" className="text-xs font-bold text-purple-700 hover:underline inline-block mt-2">
              Browse Places ➔
            </Link>
          </HoverCard>

          <HoverCard className="p-4 rounded-2xl border border-purple-100 bg-gradient-to-br from-white to-rose-50">
            <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1.5">
              <FiShield className="text-rose-600" /> Safety & Emergency
            </h4>
            <p className="text-xs text-gray-500 mt-1">Recorded hospitals and police, plus official numbers 1144, 100 and 102.</p>
            <Link to="/emergency" className="text-xs font-bold text-rose-600 hover:underline inline-block mt-2">
              Emergency Hub ➔
            </Link>
          </HoverCard>
        </div>

        <div className="pt-4 border-t border-gray-100 flex items-center justify-center gap-3">
          <Link
            to="/"
            className="btn-primary px-8 py-3 bg-purple-700 hover:bg-purple-800 text-white font-bold text-sm rounded-xl shadow-lg"
          >
            Back to Homepage
          </Link>
        </div>
      </FadeIn>
    </div>
  )
}
