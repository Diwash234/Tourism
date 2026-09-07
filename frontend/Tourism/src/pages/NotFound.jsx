import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import { FiCompass, FiHome, FiArrowRight, FiSearch } from "react-icons/fi"
import { FadeIn } from "../components/common/MotionSystem"

export default function NotFound() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center container-app py-16 px-4">
      <FadeIn className="card-base p-8 sm:p-14 max-w-xl text-center space-y-6 rounded-3xl shadow-2xl border border-[#E5E0D5] bg-white">
        <div className="relative inline-block">
          <span className="text-8xl font-black bg-gradient-to-r from-purple-700 via-rose-600 to-amber-500 bg-clip-text text-transparent">
            404
          </span>
          <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-emerald-100 text-[#102A2E] text-xs font-bold whitespace-nowrap">
            Himalayan Trail Lost
          </span>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Looks like you've wandered off the trail!
          </h1>
          <p className="text-sm text-gray-500 max-w-md mx-auto leading-relaxed">
            The page or mountain route you're looking for doesn't exist or has moved. Let's get you back on the main trail.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            to="/"
            className="w-full sm:w-auto btn-primary px-6 py-3 bg-[#102A2E] hover:bg-[#1D5146] text-white font-bold text-sm rounded-xl shadow-lg flex items-center justify-center gap-2"
          >
            <FiHome size={16} /> Return to Home
          </Link>
          <Link
            to="/destinations"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#F7F8F5] hover:bg-emerald-100 text-[#102A2E] font-bold text-sm border border-[#E5E0D5] flex items-center justify-center gap-1.5"
          >
            <FiCompass size={16} /> Explore Destinations
          </Link>
        </div>
      </FadeIn>
    </div>
  )
}
