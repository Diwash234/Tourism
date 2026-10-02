import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiAlertTriangle,
  FiX,
  FiPhone,
  FiShield,
  FiCheckCircle,
  FiActivity,
  FiArrowDown,
  FiHelpCircle
} from "react-icons/fi"

export default function AltitudeSafetyModal({ isOpen, onClose, safetyData, title }) {
  const [symptomScores, setSymptomScores] = useState({
    headache: 0,
    gastrointestinal: 0,
    fatigue: 0,
    dizziness: 0,
  })

  if (!isOpen || !safetyData) return null

  const totalScore = Object.values(symptomScores).reduce((a, b) => a + b, 0)

  const getScoreAssessment = (score) => {
    if (score <= 2) {
      return {
        label: "Normal / Mild",
        color: "text-emerald-700 bg-emerald-50 border-emerald-200",
        action: "No immediate AMS danger. Proceed with regular caution, hydration (3.5–4L/day), and sun protection.",
      }
    }
    if (score <= 5) {
      return {
        label: "Moderate Acute Mountain Sickness (AMS)",
        color: "text-amber-800 bg-amber-50 border-amber-300",
        action: "HALT ASCENT IMMEDIATELY. Rest at your current altitude for 24 hours. Drink warm fluids, take mild analgesics or Diamox. Do NOT climb higher until the score returns to 0.",
      }
    }
    return {
      label: "Severe AMS / Impending HAPE or HACE",
      color: "text-rose-800 bg-rose-50 border-rose-300",
      action: "CRITICAL MEDICAL EMERGENCY: Descend immediately by at least 500 to 1,000 meters. Administer bottled oxygen, prepare Gamow bag if available, and alert mountain rescue (1144 / HRA).",
    }
  }

  const assessment = getScoreAssessment(totalScore)

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[90vh] flex flex-col"
        >
          {/* Header */}
          <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                <FiActivity size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">High-Altitude Safety & AMS Protocol</h3>
                <p className="text-xs text-slate-400 mt-0.5">{title || "Altitude Risk Evaluation"}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
              aria-label="Close altitude safety modal"
            >
              <FiX size={20} />
            </button>
          </div>

          {/* Modal Scrollable Content */}
          <div className="p-5 sm:p-6 space-y-6 overflow-y-auto flex-1 text-sm text-slate-700">
            {/* Risk Banner */}
            <div className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
              safetyData.risk_class === "extreme"
                ? "bg-rose-50 border-rose-200 text-rose-950"
                : safetyData.risk_class === "high"
                ? "bg-amber-50 border-amber-200 text-amber-950"
                : "bg-emerald-50 border-emerald-200 text-emerald-950"
            }`}>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-black/10">
                    Risk Category: {safetyData.risk_class?.toUpperCase()}
                  </span>
                  <span className="text-xs font-bold font-mono">
                    Peak: {safetyData.max_elevation_m?.toLocaleString()}m
                  </span>
                </div>
                <p className="font-bold text-base mt-1">{safetyData.risk_level}</p>
                <p className="text-xs mt-1 opacity-90 leading-relaxed">{safetyData.summary}</p>
              </div>
            </div>

            {/* Lake Louise Self-Assessment Interactive Tool */}
            <div className="card-base p-5 bg-slate-50 border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-black text-slate-900 flex items-center gap-2">
                    <FiShield className="text-emerald-700" />
                    Lake Louise AMS Symptom Self-Assessment
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Assess your current physiological state if you are climbing above 2,500m.
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500 block">Total Score</span>
                  <span className="text-2xl font-black text-slate-900 font-mono">{totalScore} / 12</span>
                </div>
              </div>

              {/* Assessment Outcome Alert */}
              <div className={`p-3.5 rounded-xl border ${assessment.color}`}>
                <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wide">
                  <FiAlertTriangle size={15} />
                  <span>Clinical Status: {assessment.label}</span>
                </div>
                <p className="text-xs mt-1 leading-relaxed">{assessment.action}</p>
              </div>

              {/* Questions */}
              <div className="space-y-3 pt-2">
                {[
                  {
                    id: "headache",
                    label: "1. Headache",
                    options: ["0: None", "1: Mild", "2: Moderate", "3: Severe / Incapacitating"],
                  },
                  {
                    id: "gastrointestinal",
                    label: "2. Gastrointestinal (Nausea / Appetite)",
                    options: ["0: Good appetite", "1: Poor appetite / mild nausea", "2: Moderate nausea / vomiting", "3: Severe nausea"],
                  },
                  {
                    id: "fatigue",
                    label: "3. Fatigue and / or Weakness",
                    options: ["0: Normal energy", "1: Mild fatigue", "2: Moderate weakness", "3: Incapacitating exhaustion"],
                  },
                  {
                    id: "dizziness",
                    label: "4. Dizziness / Lightheadedness",
                    options: ["0: None", "1: Mild dizziness", "2: Moderate dizziness", "3: Severe dizziness / unsteady balance"],
                  },
                ].map((symptom) => (
                  <div key={symptom.id} className="bg-white p-3 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-xs font-bold text-slate-800">{symptom.label}</span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                      {symptom.options.map((opt, scoreIdx) => (
                        <button
                          key={scoreIdx}
                          type="button"
                          onClick={() => setSymptomScores((prev) => ({ ...prev, [symptom.id]: scoreIdx }))}
                          className={`py-1.5 px-2 rounded-lg text-xs font-medium border text-center transition ${
                            symptomScores[symptom.id] === scoreIdx
                              ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                              : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Golden Rules of Mountain Safety */}
            <div className="space-y-2">
              <h4 className="font-black text-slate-900 flex items-center gap-2">
                <FiCheckCircle className="text-emerald-700" />
                Golden Rules of Himalayan Acclimatization
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-600 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                {safetyData.golden_rules?.map((rule, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="font-bold text-emerald-700 shrink-0">#{idx + 1}</span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Emergency Rescue & Aid Post Directory */}
            <div className="space-y-2">
              <h4 className="font-black text-slate-900 flex items-center gap-2">
                <FiPhone className="text-rose-600" />
                Emergency Rescue & Medical Directory
              </h4>
              <div className="grid sm:grid-cols-2 gap-2.5">
                {safetyData.emergency_rescue_directory?.map((contact, idx) => (
                  <div key={idx} className="p-3 bg-white rounded-xl border border-slate-200 space-y-1">
                    <p className="font-bold text-xs text-slate-900">{contact.organization}</p>
                    <p className="text-[11px] text-slate-500">{contact.location}</p>
                    <p className="text-xs font-bold text-rose-700 font-mono">
                      {contact.phone}
                    </p>
                    <p className="text-[10px] text-slate-500 leading-tight">{contact.specialty}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="ny-btn ny-btn-primary px-6 py-2 text-xs font-bold rounded-xl"
            >
              Understood & Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
