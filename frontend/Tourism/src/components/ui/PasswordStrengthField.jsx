/**
 * PasswordStrengthField — password input with live strength watermark
 * (crack-time estimate, animated strength bar, requirement checklist).
 *
 * Props:
 *  - value, onChange: standard controlled input
 *  - showRequirements: boolean (default true) – show the checklist
 *  - label, placeholder, id, autoComplete: standard
 *  - minLength: default 8
 */
import { useMemo, useState, forwardRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiEye, FiEyeOff, FiCheck, FiAlertTriangle } from "react-icons/fi"
import { cn } from "../../utils/cn"

const REQUIREMENTS = [
  { key: "length",     label: "At least 8 characters",   test: (v) => v.length >= 8 },
  { key: "lower",      label: "One lowercase letter",     test: (v) => /[a-z]/.test(v) },
  { key: "upper",      label: "One uppercase letter",     test: (v) => /[A-Z]/.test(v) },
  { key: "number",     label: "One number",               test: (v) => /[0-9]/.test(v) },
  { key: "special",    label: "One special character",    test: (v) => /[^A-Za-z0-9]/.test(v) },
  { key: "noleading",  label: "No leading/trailing space",test: (v) => v === v.trim() && v.length > 0 },
]

const zxcvbnLikeScore = (pw) => {
  // Lightweight heuristic so we don't pull a 400kb zxcvbn bundle.
  if (!pw) return { score: 0, label: "", color: "stone" }
  let score = 0
  const met = REQUIREMENTS.filter(r => r.test(pw))
  score = Math.min(4, met.length - 1)
  if (pw.length >= 12) score = Math.min(4, score + 1)
  if (/^[a-z]+$/.test(pw)) score = Math.min(score, 1)
  if (/(.)\1{2,}/.test(pw)) score = Math.max(0, score - 1)   // repeated chars
  const common = ["password", "123456", "qwerty", "letmein", "welcome", "nepal123", "tourism"]
  if (common.some(c => pw.toLowerCase().includes(c))) score = 0
  const labels = ["Too weak", "Weak", "Fair", "Strong", "Very strong"]
  const colors = ["bg-rose-500", "bg-orange-500", "bg-amber-500", "bg-lime-500", "bg-emerald-500"]
  const textColors = ["text-rose-700", "text-orange-700", "text-amber-700", "text-lime-700", "text-emerald-700"]
  return { score, label: labels[score], color: colors[score], text: textColors[score], met }
}

const crackTimeEstimate = (pw) => {
  if (!pw) return ""
  // Rough: entropy estimate in bits
  let pool = 0
  if (/[a-z]/.test(pw)) pool += 26
  if (/[A-Z]/.test(pw)) pool += 26
  if (/[0-9]/.test(pw)) pool += 10
  if (/[^A-Za-z0-9]/.test(pw)) pool += 30
  const entropy = pw.length * Math.log2(Math.max(pool, 1))
  // 10 billion guesses/sec
  const seconds = Math.pow(2, entropy) / 1e10
  if (seconds < 1) return "Instantly cracked"
  if (seconds < 60) return `Cracked in ~${Math.round(seconds)} sec`
  if (seconds < 3600) return `Cracked in ~${Math.round(seconds / 60)} min`
  if (seconds < 86400) return `Cracked in ~${Math.round(seconds / 3600)} hr`
  if (seconds < 86400 * 30) return `Cracked in ~${Math.round(seconds / 86400)} days`
  if (seconds < 86400 * 365) return `Cracked in ~${Math.round(seconds / (86400 * 30))} months`
  if (seconds < 86400 * 365 * 100) return `Cracked in ~${Math.round(seconds / (86400 * 365))} years`
  if (seconds < 86400 * 365 * 1e6) return `Cracked in ~${Math.round(seconds / (86400 * 365 * 1000))}k years`
  return "Centuries to crack"
}

// eslint-disable-next-line react/display-name
const PasswordStrengthField = forwardRef((
  { value = "", onChange, label = "Password", placeholder = "Create a password", id = "password", autoComplete = "new-password", showRequirements = true, minLength = 8, className = "", name, ...rest }, ref,
) => {
  const [visible, setVisible] = useState(false)
  const [focused, setFocused] = useState(false)
  const s = useMemo(() => zxcvbnLikeScore(value), [value])
  const crack = useMemo(() => crackTimeEstimate(value), [value])

  return (
    <div className={cn("w-full", className)}>
      {label && (
        <label htmlFor={id} className="block text-sm font-semibold text-stone-800 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          ref={ref}
          id={id}
          name={name}
          type={visible ? "text" : "password"}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          minLength={minLength}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          className="input-field pr-11 w-full"
          {...rest}
        />
        <button
          type="button"
          onClick={() => setVisible(v => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-500 hover:text-stone-800 transition"
        >
          {visible ? <FiEyeOff /> : <FiEye />}
        </button>
      </div>

      {/* Strength bar */}
      {value && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-stone-200 overflow-hidden">
            <motion.div
              initial={false}
              animate={{ width: `${((s.score + 1) / 5) * 100}%` }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={cn("h-full rounded-full", s.color)}
            />
          </div>
          <span className={cn("text-xs font-bold", s.text)}>{s.label}</span>
        </div>
      )}

      {/* Crack time watermark */}
      {value && (
        <div className="mt-1 flex items-center gap-1.5 text-[11px] text-stone-500">
          <FiAlertTriangle size={12} className={value && s.score < 2 ? "text-rose-500" : "text-emerald-500"} />
          <span>{crack}</span>
        </div>
      )}

      {/* Requirements checklist */}
      <AnimatePresence>
        {showRequirements && (focused || value) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
              {REQUIREMENTS.map(r => {
                const ok = r.test(value)
                return (
                  <li key={r.key} className={cn("flex items-center gap-1.5", ok ? "text-emerald-700" : "text-stone-500")}>
                    <span className={cn(
                      "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0",
                      ok ? "bg-emerald-100 text-emerald-700" : "bg-stone-100 text-stone-400",
                    )}>
                      <FiCheck size={11} strokeWidth={3} />
                    </span>
                    {r.label}
                  </li>
                )
              })}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})

export default PasswordStrengthField
