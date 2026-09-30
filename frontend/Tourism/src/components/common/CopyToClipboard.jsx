import { useState } from "react"
import { FiCopy, FiCheck } from "react-icons/fi"

/**
 * Copy to clipboard button with success feedback.
 */
export default function CopyToClipboard({ text, label = "Copy", className = "" }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea")
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand("copy")
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
        copied
          ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
          : "border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700"
      } ${className}`}
      aria-label={copied ? "Copied" : label}
    >
      {copied ? <FiCheck size={14} /> : <FiCopy size={14} />}
      {copied ? "Copied!" : label}
    </button>
  )
}
