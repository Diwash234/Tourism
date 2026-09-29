import { useEffect, useState } from "react"
import { FiX, FiCommand } from "react-icons/fi"

const SHORTCUTS = [
  { keys: ["Ctrl", "K"], description: "Focus search" },
  { keys: ["Ctrl", "D"], description: "Toggle dark/light theme" },
  { keys: ["Ctrl", "/"], description: "Show this help" },
  { keys: ["G", "D"], description: "Go to Dashboard" },
  { keys: ["G", "H"], description: "Go to Home" },
  { keys: ["G", "E"], description: "Go to Explore" },
  { keys: ["G", "P"], description: "Go to Trip Planner" },
  { keys: ["Esc"], description: "Close menus and dialogs" },
]

export default function KeyboardShortcutsModal() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handler = () => setOpen(true)
    window.addEventListener("ny:show-shortcuts", handler)
    return () => window.removeEventListener("ny:show-shortcuts", handler)
  }, [])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Keyboard shortcuts">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-md rounded-2xl bg-white dark:bg-slate-800 shadow-2xl border border-gray-200 dark:border-slate-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FiCommand size={20} className="text-emerald-600" />
            Keyboard Shortcuts
          </h2>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            aria-label="Close"
          >
            <FiX size={18} />
          </button>
        </div>
        <div className="space-y-2">
          {SHORTCUTS.map(({ keys, description }) => (
            <div key={description} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-slate-700 last:border-0">
              <span className="text-sm text-gray-700 dark:text-gray-300">{description}</span>
              <div className="flex items-center gap-1">
                {keys.map((key) => (
                  <kbd key={key} className="px-2 py-1 text-xs font-mono font-bold bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-md border border-gray-200 dark:border-slate-600 shadow-sm">
                    {key}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
