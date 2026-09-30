import { useState } from "react"
import { FiCopy, FiCheck } from "react-icons/fi"
import { useToast } from "./Toast"

/**
 * Copy-to-clipboard button with success feedback.
 */
export default function CopyButton({ text, label = "Copy", className = "" }) {
  const [copied, setCopied] = useState(false)
  const { addToast } = useToast()

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      addToast("Copied to clipboard!", "success")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      addToast("Failed to copy", "error")
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors ${className}`}
      aria-label={copied ? "Copied" : label}
    >
      {copied ? <FiCheck size={14} className="text-emerald-500" /> : <FiCopy size={14} />}
      {copied ? "Copied!" : label}
    </button>
  )
}
