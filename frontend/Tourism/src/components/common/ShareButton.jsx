import { useState } from "react"
import { FiShare2, FiCheck, FiCopy, FiTwitter, FiFacebook } from "react-icons/fi"
import useToast from "../../hooks/useToast"

/**
 * Share button with native Web Share API fallback to copy link.
 * Supports Twitter and Facebook sharing.
 */
export default function ShareButton({ title, text, url, variant = "default" }) {
  const [copied, setCopied] = useState(false)
  const { addToast } = useToast()

  const shareUrl = url || window.location.href
  const shareTitle = title || document.title
  const shareText = text || ""

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title: shareTitle, text: shareText, url: shareUrl })
      } catch (err) {
        if (err.name !== "AbortError") {
          copyToClipboard()
        }
      }
    } else {
      copyToClipboard()
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      addToast("Link copied to clipboard!", "success")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      addToast("Failed to copy link", "error")
    }
  }

  const shareToTwitter = () => {
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
      "_blank",
      "width=550,height=420"
    )
  }

  const shareToFacebook = () => {
    window.open(
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
      "_blank",
      "width=550,height=420"
    )
  }

  if (variant === "mobile") {
    return (
      <div className="space-y-2">
        <button
          type="button"
          onClick={handleNativeShare}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors"
        >
          {copied ? <FiCheck size={16} className="text-emerald-400" /> : <FiShare2 size={16} />}
          {copied ? "Copied!" : "Share"}
        </button>
        <button
          type="button"
          onClick={copyToClipboard}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors"
        >
          <FiCopy size={16} />
          Copy Link
        </button>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={shareToTwitter}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors"
          >
            <FiTwitter size={14} /> Twitter
          </button>
          <button
            type="button"
            onClick={shareToFacebook}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors"
          >
            <FiFacebook size={14} /> Facebook
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={handleNativeShare}
        className="p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label="Share"
        title="Share"
      >
        {copied ? <FiCheck size={18} className="text-emerald-400" /> : <FiShare2 size={18} />}
      </button>
      <button
        type="button"
        onClick={shareToTwitter}
        className="p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label="Share on Twitter"
        title="Share on Twitter"
      >
        <FiTwitter size={18} />
      </button>
      <button
        type="button"
        onClick={shareToFacebook}
        className="p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label="Share on Facebook"
        title="Share on Facebook"
      >
        <FiFacebook size={18} />
      </button>
    </div>
  )
}
