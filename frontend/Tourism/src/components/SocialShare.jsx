import { useState, useCallback, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiShare2, FiLink, FiCheck, FiX, FiDownload,
  FiFacebook, FiTwitter, FiLinkedin, FiMessageCircle,
} from "react-icons/fi"
import useToast from "../hooks/useToast"

// ─── Share Count Display ─────────────────────────────────────────────────────
const ShareCount = ({ count, label = "shares" }) => (
  <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
    <FiShare2 size={12} />
    <span>{count.toLocaleString()} {label}</span>
  </div>
)

// ─── QR Code Generator (simple SVG-based) ────────────────────────────────────
const QRCode = ({ value, size = 120 }) => {
  // Simple QR-like pattern generator for demo purposes
  // In production, use a proper QR library like qrcode.react
  const cells = useMemo(() => {
    const grid = []
    const size = 21
    for (let i = 0; i < size; i++) {
      for (let j = 0; j < size; j++) {
        // Create a deterministic pattern based on the value
        const charCode = value.charCodeAt((i * j) % value.length) || 0
        if ((i * j + charCode) % 3 === 0) {
          grid.push({ x: i, y: j })
        }
      }
    }
    // Add corner markers
    const markers = [
      { x: 0, y: 0 }, { x: 14, y: 0 }, { x: 0, y: 14 },
    ]
    markers.forEach(({ x, y }) => {
      for (let i = 0; i < 7; i++) {
        for (let j = 0; j < 7; j++) {
          if (i === 0 || i === 6 || j === 0 || j === 6 || (i >= 2 && i <= 4 && j >= 2 && j <= 4)) {
            grid.push({ x: x + i, y: y + j })
          }
        }
      }
    })
    return grid
  }, [value])

  const cellSize = size / 21

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rounded-lg">
      <rect width={size} height={size} fill="white" />
      {cells.map((cell, i) => (
        <rect
          key={i}
          x={cell.x * cellSize}
          y={cell.y * cellSize}
          width={cellSize}
          height={cellSize}
          fill="#1B8A5A"
        />
      ))}
    </svg>
  )
}

// ─── Open Graph Preview ──────────────────────────────────────────────────────
const OGPreview = ({ url, title, description, image }) => (
  <div className="border border-gray-200 rounded-xl overflow-hidden bg-white max-w-sm">
    {image && (
      <div className="h-32 bg-gray-100 overflow-hidden">
        <img src={image} alt="" className="w-full h-full object-cover" />
      </div>
    )}
    <div className="p-3">
      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{url}</p>
      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{title}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{description}</p>
    </div>
  </div>
)

// ─── Social Share Component ──────────────────────────────────────────────────
const SocialShare = ({
  url,
  title = "Check out this amazing destination!",
  description = "Discover the beauty of Nepal",
  image,
  shareCount = 0,
  showQR = true,
  showOGPreview = true,
  className = "",
}) => {
  const { showToast } = useToast()
  const [showModal, setShowModal] = useState(false)
  const [copied, setCopied] = useState(false)

  const shareUrl = url || (typeof window !== "undefined" ? window.location.href : "")
  const encodedUrl = encodeURIComponent(shareUrl)
  const encodedTitle = encodeURIComponent(title)

  const shareLinks = useMemo(() => [
    {
      id: "facebook",
      label: "Facebook",
      icon: FiFacebook,
      color: "#1877F2",
      href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
    },
    {
      id: "twitter",
      label: "Twitter",
      icon: FiTwitter,
      color: "#1DA1F2",
      href: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`,
    },
    {
      id: "whatsapp",
      label: "WhatsApp",
      icon: FiMessageCircle,
      color: "#25D366",
      href: `https://wa.me/?text=${encodedTitle}%20${encodedUrl}`,
    },
    {
      id: "linkedin",
      label: "LinkedIn",
      icon: FiLinkedin,
      color: "#0A66C2",
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
    },
  ], [encodedUrl, encodedTitle])

  const handleCopyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      showToast("Link copied to clipboard!", "success")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast("Failed to copy link", "error")
    }
  }, [shareUrl, showToast])

  const handleShare = useCallback(async (platform) => {
    if (platform === "native" && navigator.share) {
      try {
        await navigator.share({ title, text: description, url: shareUrl })
      } catch {
        // User cancelled or share failed
      }
    } else {
      const link = shareLinks.find((l) => l.id === platform)
      if (link) {
        window.open(link.href, "_blank", "noopener,noreferrer,width=600,height=400")
      }
    }
  }, [shareLinks, title, description, shareUrl])

  const handleDownloadQR = useCallback(() => {
    const svg = document.querySelector("[data-qr-svg]")
    if (!svg) return
    const svgData = new XMLSerializer().serializeToString(svg)
    const blob = new Blob([svgData], { type: "image/svg+xml" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = "share-qr.svg"
    link.click()
    URL.revokeObjectURL(link.href)
    showToast("QR code downloaded", "success")
  }, [showToast])

  return (
    <div className={className}>
      {/* Share Button */}
      <button
        onClick={() => setShowModal(true)}
        className="btn-secondary flex items-center gap-2"
      >
        <FiShare2 size={16} />
        Share
        {shareCount > 0 && <ShareCount count={shareCount} />}
      </button>

      {/* Share Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-6"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900">Share this page</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiX size={20} />
                </button>
              </div>

              {/* Social Buttons */}
              <div className="grid grid-cols-4 gap-3">
                {shareLinks.map((link) => {
                  const Icon = link.icon
                  return (
                    <button
                      key={link.id}
                      onClick={() => handleShare(link.id)}
                      className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center text-white"
                        style={{ backgroundColor: link.color }}
                      >
                        <Icon size={20} />
                      </div>
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{link.label}</span>
                    </button>
                  )
                })}
              </div>

              {/* Copy Link */}
              <div className="flex items-center gap-2">
                <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <FiLink size={14} className="text-gray-400 flex-shrink-0" />
                  <span className="text-sm text-gray-600 dark:text-gray-300 truncate">{shareUrl}</span>
                </div>
                <button
                  onClick={handleCopyLink}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    copied
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                  }`}
                >
                  {copied ? <FiCheck size={16} /> : "Copy"}
                </button>
              </div>

              {/* QR Code */}
              {showQR && (
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                  <div data-qr-svg>
                    <QRCode value={shareUrl} size={100} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Scan to share on mobile</p>
                    <p className="text-xs text-gray-500 mt-1">Point your camera at the QR code to open this page on your phone.</p>
                    <button
                      onClick={handleDownloadQR}
                      className="mt-2 text-xs text-emerald-600 font-medium flex items-center gap-1 hover:underline"
                    >
                      <FiDownload size={12} /> Download QR
                    </button>
                  </div>
                </div>
              )}

              {/* OG Preview */}
              {showOGPreview && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Preview</p>
                  <OGPreview url={shareUrl} title={title} description={description} image={image} />
                </div>
              )}

              {/* Native Share (if available) */}
              {typeof navigator !== "undefined" && navigator.share && (
                <button
                  onClick={() => handleShare("native")}
                  className="w-full btn-secondary py-2.5 text-sm"
                >
                  More options...
                </button>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default SocialShare
