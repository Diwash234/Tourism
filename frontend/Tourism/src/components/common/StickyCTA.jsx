import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link, useLocation } from "react-router-dom"
import { FiCompass, FiShield, FiPhoneCall, FiArrowRight, FiZap } from "react-icons/fi"

export default function StickyCTA() {
  const [visible, setVisible] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 380) {
        setVisible(true)
      } else {
        setVisible(false)
      }
    }
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Hide on admin or emergency page to avoid distraction
  if (location.pathname.startsWith("/admin") || location.pathname === "/emergency") {
    return null
  }

  return (
    <>
      {/* Desktop Floating Sticky CTA */}
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="hidden md:flex fixed bottom-6 left-1/2 -translate-x-1/2 z-40 items-center gap-4 px-5 py-2.5 rounded-full bg-gray-950/90 text-white border border-purple-500/40 shadow-2xl backdrop-blur-md"
          >
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-bold text-gray-200">
                Planning a trip to Nepal?
              </span>
              <span className="text-[11px] text-amber-300 font-semibold bg-amber-400/10 px-2 py-0.5 rounded-full border border-amber-400/20">
                ⚡ 24/7 Helpline: 1144
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/destinations"
                className="px-4 py-1.5 rounded-full bg-gradient-to-r from-amber-400 to-amber-500 text-gray-950 text-xs font-black hover:scale-105 transition-all shadow flex items-center gap-1"
              >
                <FiCompass size={13} /> Explore Places <FiArrowRight size={12} />
              </Link>
              <Link
                to="/budget-estimator"
                className="px-3.5 py-1.5 rounded-full bg-purple-900/80 hover:bg-purple-800 text-purple-200 text-xs font-bold border border-purple-700/60 transition-colors"
              >
                Estimate Cost
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Fixed Bottom Safe-Area Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-gray-200 px-4 py-2.5 flex items-center justify-between gap-3 shadow-2xl pb-[max(0.65rem,env(safe-area-inset-bottom))]">
        <Link
          to="/destinations"
          className="flex-1 py-2.5 px-3 rounded-xl bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold text-center flex items-center justify-center gap-1.5 shadow-md shadow-purple-900/20"
        >
          <FiCompass size={14} /> Explore places
        </Link>
        <Link
          to="/emergency"
          className="py-2.5 px-3.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center justify-center gap-1 shrink-0 shadow-md shadow-rose-600/20"
        >
          <FiShield size={14} /> SOS
        </Link>
      </div>
    </>
  )
}
