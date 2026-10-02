import { useState } from "react"
import { FiShare2, FiTwitter, FiFacebook, FiLinkedin, FiLink, FiCheck } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"

/**
 * Social sharing component with native Web Share API fallback.
 * Supports Twitter, Facebook, LinkedIn, and copy-to-clipboard.
 */
export default function SocialShare({ title, text, url, className = "" }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const [open, setOpen] = useState(false)

  const shareUrl = url || window.location.href
  const shareText = text || title || document.title

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, text: shareText, url: shareUrl })
        setOpen(false)
      } catch {
        // User cancelled or share failed
      }
    } else {
      setOpen(v => !v)
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea")
      textarea.value = shareUrl
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand("copy")
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
    setOpen(false)
  }

  const shareLinks = [
    {
      name: "Twitter",
      icon: FiTwitter,
      url: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
      color: "hover:bg-blue-50 hover:text-blue-500",
    },
    {
      name: "Facebook",
      icon: FiFacebook,
      url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
      color: "hover:bg-blue-50 hover:text-blue-600",
    },
    {
      name: "LinkedIn",
      icon: FiLinkedin,
      url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
      color: "hover:bg-blue-50 hover:text-blue-700",
    },
  ]

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        type="button"
        onClick={handleNativeShare}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
        aria-label="Share"
        aria-expanded={open}
      >
        <FiShare2 size={16} />
        <span className="hidden sm:inline">{t("common.share")}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl z-50 py-1">
          {shareLinks.map(link => (
            <a
              key={link.name}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpen(false)}
              className={`flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 transition-colors ${link.color}`}
            >
              <link.icon size={16} />
              {link.name}
            </a>
          ))}
          <button
            type="button"
            onClick={copyToClipboard}
            className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            {copied ? <FiCheck size={16} className="text-emerald-500" /> : <FiLink size={16} />}
            {copied ? "Copied!" : "Copy link"}
          </button>
        </div>
      )}
    </div>
  )
}
