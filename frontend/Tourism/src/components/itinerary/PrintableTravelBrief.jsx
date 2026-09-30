import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiPrinter,
  FiX,
  FiPhone,
  FiShield,
  FiMapPin,
  FiCalendar,
  FiCompass,
  FiFileText,
  FiHeart
} from "react-icons/fi"

export default function PrintableTravelBrief({
  isOpen,
  onClose,
  plan
}) {
  const effectivePlan = plan || {
    title: "Nepal Emergency Safety Dossier & Field Brief",
    summary: "Official emergency contact directory, traveler medical ID card, and mountain preparedness guidelines for travel across Nepal.",
    days: "Expedition / Travel Record",
    pace: "Safety-First",
    best_season: "Spring / Autumn",
    estimated_cost: "NPR 0",
    altitude_safety: {
      max_elevation_m: 5545,
      acclimatization_days: 2,
      risk_level: "Moderate to High",
      advice: "Drink 4-5 liters of water daily. Never ascend more than 500m per day above 2,500m. If AMS symptoms develop, descend immediately."
    },
    itinerary: []
  }

  const [personalDetails, setPersonalDetails] = useState({
    fullName: "",
    nationality: effectivePlan.nationality || "Nepali",
    bloodGroup: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    insuranceCompany: "",
    insurancePolicyNumber: "",
  })

  if (!isOpen) return null

  const days = effectivePlan.itinerary || []
  const maxElev = effectivePlan.altitude_safety?.max_elevation_m || effectivePlan.max_elevation_m

  const handlePrint = () => {
    window.print()
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.96 }}
          className="relative w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[94vh] flex flex-col"
        >
          {/* Web-Only Header */}
          <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0 print:hidden">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <FiFileText size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">Offline Field Dossier & Travel Brief</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Print or save as PDF to keep on your smartphone when offline in the mountains
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePrint}
                className="ny-btn ny-btn-primary flex items-center gap-2 text-xs font-bold py-2 px-4 rounded-xl shadow-md"
              >
                <FiPrinter size={15} />
                <span>Print / Save PDF</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
                aria-label="Close printable brief"
              >
                <FiX size={20} />
              </button>
            </div>
          </div>

          {/* Printable Document Body */}
          <div className="p-6 sm:p-8 space-y-6 overflow-y-auto flex-1 text-slate-900 font-sans print:p-0 print:overflow-visible">
            {/* Document Header Banner */}
            <div className="border-b-2 border-slate-900 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="text-[10px] uppercase font-black tracking-widest text-emerald-800 block">
                    Nepal National Tourism Expedition Record · यात्रा विवरण
                  </span>
                  <h1 className="text-2xl font-black tracking-tight mt-1">
                    {effectivePlan.title}
                  </h1>
                  {effectivePlan.title_nepali && (
                    <p className="text-sm font-bold text-slate-600 mt-0.5">{effectivePlan.title_nepali}</p>
                  )}
                </div>
                <div className="text-right text-xs shrink-0">
                  <span className="font-bold block">Document Type: Official Field Dossier</span>
                  <span className="text-slate-500 block">Date: {new Date().toLocaleDateString()}</span>
                  <span className="text-emerald-800 font-black uppercase text-[11px] block mt-1">
                    Verified Nepal Yatra Route
                  </span>
                </div>
              </div>

              {/* Key Route Metrics */}
              <div className="grid grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-200 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-black block">Duration</span>
                  <span className="font-black text-sm">{effectivePlan.days || days.length || "Expedition"} Days</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-black block">Max Elevation</span>
                  <span className="font-black text-sm text-emerald-800">
                    {maxElev ? `${maxElev.toLocaleString()}m` : "Sub-Alpine"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-black block">Nationality Tier</span>
                  <span className="font-bold text-sm capitalize">
                    {effectivePlan.nationality === "nepali" ? "Domestic (नेपाली)" : effectivePlan.nationality || "International"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-black block">Total Estimated Cost</span>
                  <span className="font-mono font-bold text-sm">
                    {effectivePlan.total_budget_npr ? `NPR ${effectivePlan.total_budget_npr.toLocaleString()}` : "Market Rate"}
                  </span>
                </div>
              </div>
            </div>

            {/* Traveler Field Emergency SOS Card (Fillable on web, prints clearly) */}
            <div className="border-2 border-rose-600 rounded-2xl p-4 bg-rose-50/40 space-y-3">
              <div className="flex items-center justify-between border-b border-rose-200 pb-2">
                <div className="flex items-center gap-2 text-rose-900 font-black text-xs uppercase tracking-wide">
                  <FiHeart className="text-rose-600" />
                  <span>Traveler Emergency Medical & Insurance SOS Card</span>
                </div>
                <span className="text-[10px] text-rose-700 font-bold">Keep with Passport</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase block">Traveler Full Name</label>
                  <input
                    type="text"
                    value={personalDetails.fullName}
                    onChange={(e) => setPersonalDetails({ ...personalDetails, fullName: e.target.value })}
                    placeholder="Enter full name"
                    className="w-full bg-white border border-slate-300 rounded-lg px-2 py-1 text-xs font-bold text-slate-900 print:border-none print:p-0"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase block">Blood Group</label>
                  <input
                    type="text"
                    value={personalDetails.bloodGroup}
                    onChange={(e) => setPersonalDetails({ ...personalDetails, bloodGroup: e.target.value })}
                    placeholder="e.g. O+ / A+"
                    className="w-full bg-white border border-slate-300 rounded-lg px-2 py-1 text-xs font-bold text-slate-900 print:border-none print:p-0"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase block">Emergency Contact Phone</label>
                  <input
                    type="text"
                    value={personalDetails.emergencyContactPhone}
                    onChange={(e) => setPersonalDetails({ ...personalDetails, emergencyContactPhone: e.target.value })}
                    placeholder="+Country Phone Number"
                    className="w-full bg-white border border-slate-300 rounded-lg px-2 py-1 text-xs font-bold text-slate-900 print:border-none print:p-0"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase block">Insurance Policy #</label>
                  <input
                    type="text"
                    value={personalDetails.insurancePolicyNumber}
                    onChange={(e) => setPersonalDetails({ ...personalDetails, insurancePolicyNumber: e.target.value })}
                    placeholder="Policy / Hotline"
                    className="w-full bg-white border border-slate-300 rounded-lg px-2 py-1 text-xs font-bold text-slate-900 print:border-none print:p-0"
                  />
                </div>
              </div>
            </div>

            {/* National Emergency Hotline Directory */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs border border-slate-200 p-3 rounded-2xl bg-slate-50">
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Nepal Tourist Police</span>
                <span className="font-mono font-black text-sm text-slate-900">1144</span>
                <span className="text-[10px] text-slate-500 block">Toll-free in Nepal</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Himalayan Rescue (HRA)</span>
                <span className="font-mono font-black text-sm text-slate-900">+977-1-4440292</span>
                <span className="text-[10px] text-slate-500 block">Kathmandu HQ</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">APF Disaster Rescue</span>
                <span className="font-mono font-black text-sm text-slate-900">1114</span>
                <span className="text-[10px] text-slate-500 block">Mountain & Flood Ops</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Nepal Police Emergency</span>
                <span className="font-mono font-black text-sm text-slate-900">100</span>
                <span className="text-[10px] text-slate-500 block">National Hotline</span>
              </div>
            </div>

            {/* Day-by-Day Walking Schedule Table */}
            <div className="space-y-2">
              <h3 className="text-sm font-black uppercase tracking-wider text-slate-900">
                Day-by-Day Expedition Schedule & Walking Stages
              </h3>
              <table className="w-full text-left text-xs border-collapse border border-slate-200">
                <thead>
                  <tr className="bg-slate-900 text-white uppercase text-[10px] font-black">
                    <th className="p-2 border border-slate-800 w-12 text-center">Day</th>
                    <th className="p-2 border border-slate-800">Stage / Destination</th>
                    <th className="p-2 border border-slate-800 w-24">Altitude</th>
                    <th className="p-2 border border-slate-800">Activity & Route Notes</th>
                    <th className="p-2 border border-slate-800 w-28">Overnight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {days.map((d, idx) => {
                    const firstDest = d.destinations?.[0] || {}
                    const elev = firstDest.elevation_m || d.elevation_m
                    return (
                      <tr key={idx} className="hover:bg-slate-50 align-top">
                        <td className="p-2 border border-slate-200 font-black text-center text-amber-700">
                          #{d.day_number || idx + 1}
                        </td>
                        <td className="p-2 border border-slate-200 font-bold">
                          {d.title || firstDest.name}
                        </td>
                        <td className="p-2 border border-slate-200 font-mono font-bold text-emerald-800">
                          {elev ? `${elev.toLocaleString()}m` : "—"}
                        </td>
                        <td className="p-2 border border-slate-200 text-slate-600 leading-snug">
                          {d.activity || firstDest.short_description || "Trek itinerary milestone"}
                        </td>
                        <td className="p-2 border border-slate-200 text-slate-700 font-medium">
                          {d.stay || firstDest.city || "Lodge / Tea House"}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Offline Essential Phrases & Mountain Rules */}
            <div className="grid sm:grid-cols-2 gap-4 text-xs pt-2">
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 space-y-1.5">
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px] block">
                  🗣️ Essential Offline Nepali Phrases
                </span>
                <ul className="space-y-1 text-[11px] text-slate-700">
                  <li>• <b>Namaste</b> (नमस्ते): Hello / Greetings (palms together)</li>
                  <li>• <b>Bistārai jānuhos</b> (बिस्तारै जानुहोस्): Walk slowly (vital for AMS!)</li>
                  <li>• <b>Malāī ringaṭā lāgyo</b> (मलाई रिंगटा लाग्यो): I feel dizzy / altitude sick</li>
                  <li>• <b>Pānī umāleko ho?</b> (पानी उमालेको हो?): Is this water boiled?</li>
                  <li>• <b>Dherai dhanyabād</b> (धेरै धन्यवाद): Thank you very much</li>
                </ul>
              </div>

              <div className="p-3 bg-amber-50/70 rounded-2xl border border-amber-200 space-y-1.5">
                <span className="font-bold text-amber-950 uppercase tracking-wider text-[11px] block">
                  🏔️ Critical Himalayan Trail Rules
                </span>
                <ul className="space-y-1 text-[11px] text-amber-900">
                  <li>• <b>Yak Rule:</b> Stand on the inner mountain cliffside when animals pass.</li>
                  <li>• <b>Mani Stones:</b> Walk clockwise keeping chortens on your right.</li>
                  <li>• <b>Hydration:</b> Drink 3.5 to 4 liters of fluid daily above 3,000m.</li>
                  <li>• <b>AMS Rule:</b> Never ascend to sleep higher with altitude symptoms.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Web Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0 print:hidden">
            <span className="text-xs text-slate-500">
              💡 Printing or saving as PDF formats automatically to A4 pages.
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="ny-btn ny-btn-secondary px-5 py-2 text-xs font-bold rounded-xl"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handlePrint}
                className="ny-btn ny-btn-primary flex items-center gap-1.5 px-5 py-2 text-xs font-bold rounded-xl"
              >
                <FiPrinter size={14} />
                <span>Print Document</span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
