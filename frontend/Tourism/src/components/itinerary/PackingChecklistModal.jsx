import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCheckSquare,
  FiSquare,
  FiX,
  FiPrinter,
  FiRefreshCw,
  FiShield,
  FiShoppingBag,
  FiInfo,
  FiTag
} from "react-icons/fi"
import useToast from "../../hooks/useToast"

export default function PackingChecklistModal({
  isOpen,
  onClose,
  packingData,
  title,
  slug
}) {
  const { showToast } = useToast()
  const [activeCategory, setActiveCategory] = useState("all")
  const [packedItems, setPackedItems] = useState({})
  const [showRentalGuide, setShowRentalGuide] = useState(false)

  const storageKey = `ny_pack_${slug || "default"}`

  useEffect(() => {
    if (!isOpen) return
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        setPackedItems(JSON.parse(saved))
      }
    } catch {
      // ignore
    }
  }, [isOpen, storageKey])

  if (!isOpen || !packingData) return null

  const allItems = packingData.all_items || []
  const categories = packingData.categories || {}
  const rentalGuide = packingData.rental_guide || {}

  const toggleItem = (itemName) => {
    setPackedItems((prev) => {
      const next = { ...prev, [itemName]: !prev[itemName] }
      try {
        localStorage.setItem(storageKey, JSON.stringify(next))
      } catch {
        // ignore
      }
      return next
    })
  }

  const resetChecklist = () => {
    setPackedItems({})
    try {
      localStorage.removeItem(storageKey)
    } catch {
      // ignore
    }
    showToast("Checklist reset", "info")
  }

  const checkAll = () => {
    const full = {}
    allItems.forEach((it) => {
      full[it.item] = true
    })
    setPackedItems(full)
    try {
      localStorage.setItem(storageKey, JSON.stringify(full))
    } catch {
      // ignore
    }
    showToast("All items marked packed", "success")
  }

  const itemsToDisplay =
    activeCategory === "all"
      ? allItems
      : categories[activeCategory] || []

  const packedCount = allItems.filter((it) => packedItems[it.item]).length
  const pct = allItems.length > 0 ? Math.round((packedCount / allItems.length) * 100) : 0

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-3xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[92vh] flex flex-col"
        >
          {/* Header */}
          <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <FiCheckSquare size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">Interactive Packing Checklist</h3>
                <p className="text-xs text-slate-400 mt-0.5">{title || "Trekking & Expedition Gear"}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
              aria-label="Close packing checklist modal"
            >
              <FiX size={20} />
            </button>
          </div>

          {/* Progress Banner & Quick Actions */}
          <div className="p-4 bg-slate-50 border-b border-slate-200 space-y-3 shrink-0">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-xs font-bold text-slate-600">Packing Progress:</span>
                <span className="text-lg font-black text-emerald-800 font-mono">
                  {packedCount} / {allItems.length}
                </span>
                <span className="text-xs text-slate-500 font-semibold">({pct}%)</span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setShowRentalGuide(!showRentalGuide)}
                  className={`px-3 py-1 text-xs font-bold rounded-xl border flex items-center gap-1 transition ${
                    showRentalGuide
                      ? "bg-amber-100 text-amber-900 border-amber-300"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <FiShoppingBag size={12} />
                  <span>{showRentalGuide ? "Hide Rental Guide" : "Local Rental Guide"}</span>
                </button>
                <button
                  type="button"
                  onClick={checkAll}
                  className="px-2.5 py-1 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-100"
                >
                  Check All
                </button>
                <button
                  type="button"
                  onClick={resetChecklist}
                  className="px-2.5 py-1 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-100"
                >
                  Reset
                </button>
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-2.5 py-1 text-xs font-semibold rounded-xl bg-slate-900 text-white hover:bg-slate-800 flex items-center gap-1"
                >
                  <FiPrinter size={12} />
                  <span className="hidden sm:inline">Print</span>
                </button>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>

            {/* Category Filter Pills */}
            <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
              {[
                { key: "all", label: "All Items" },
                { key: "clothing", label: "Clothing & Layers" },
                { key: "hardware", label: "Footwear & Hardware" },
                { key: "health", label: "Health & Altitude" },
                { key: "electronics", label: "Electronics" },
                { key: "docs_and_cash", label: "Docs & Cash" },
              ].map((cat) => (
                <button
                  key={cat.key}
                  type="button"
                  onClick={() => setActiveCategory(cat.key)}
                  className={`px-3 py-1 rounded-xl whitespace-nowrap font-bold transition ${
                    activeCategory === cat.key
                      ? "bg-emerald-800 text-white"
                      : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Checklist */}
          <div className="p-5 sm:p-6 space-y-4 overflow-y-auto flex-1">
            {/* Thamel & Pokhara Rental Guide Card (if toggled) */}
            {showRentalGuide && (
              <div className="card-base p-4 bg-amber-50/70 border border-amber-200 space-y-3">
                <div className="flex items-center gap-2">
                  <FiShoppingBag className="text-amber-800" size={16} />
                  <h4 className="font-black text-sm text-amber-950">
                    Kathmandu & Pokhara Local Gear Rental Advice
                  </h4>
                </div>
                <p className="text-xs text-amber-900 leading-relaxed">
                  You don't need to purchase expensive high-altitude down gear before arriving. Reputable gear shops in <b>Thamel (Kathmandu)</b> and <b>Lakeside (Pokhara)</b> rent high-quality equipment on a daily basis.
                </p>

                <div className="grid sm:grid-cols-2 gap-3 text-xs pt-1">
                  <div className="bg-white p-3 rounded-xl border border-amber-200 space-y-1.5">
                    <p className="font-bold text-slate-900">📍 Kathmandu (Thamel):</p>
                    <p className="text-[11px] text-slate-600">{rentalGuide.thamel_kathmandu?.location}</p>
                    <ul className="space-y-0.5 text-[11px] text-slate-700">
                      <li>• Down Jacket (-20°C): <b>{rentalGuide.thamel_kathmandu?.rates?.down_jacket}</b></li>
                      <li>• Sleeping Bag (-20°C): <b>{rentalGuide.thamel_kathmandu?.rates?.sleeping_bag_neg20}</b></li>
                      <li>• Trekking Poles: <b>{rentalGuide.thamel_kathmandu?.rates?.trekking_poles_pair}</b></li>
                    </ul>
                    <p className="text-[10px] text-slate-500 italic pt-1">{rentalGuide.thamel_kathmandu?.tips}</p>
                  </div>

                  <div className="bg-white p-3 rounded-xl border border-amber-200 space-y-1.5">
                    <p className="font-bold text-slate-900">📍 Pokhara (Lakeside):</p>
                    <p className="text-[11px] text-slate-600">{rentalGuide.lakeside_pokhara?.location}</p>
                    <ul className="space-y-0.5 text-[11px] text-slate-700">
                      <li>• Down Jacket: <b>{rentalGuide.lakeside_pokhara?.rates?.down_jacket}</b></li>
                      <li>• Sleeping Bag: <b>{rentalGuide.lakeside_pokhara?.rates?.sleeping_bag}</b></li>
                      <li>• Trekking Poles: <b>{rentalGuide.lakeside_pokhara?.rates?.trekking_poles}</b></li>
                    </ul>
                    <p className="text-[10px] text-slate-500 italic pt-1">{rentalGuide.lakeside_pokhara?.tips}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Checklist Items */}
            <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 overflow-hidden bg-white">
              {itemsToDisplay.map((item, idx) => {
                const isChecked = !!packedItems[item.item]
                return (
                  <div
                    key={idx}
                    onClick={() => toggleItem(item.item)}
                    className={`p-3.5 flex items-start gap-3 cursor-pointer transition select-none ${
                      isChecked ? "bg-emerald-50/50" : "hover:bg-slate-50"
                    }`}
                  >
                    <button
                      type="button"
                      className="mt-0.5 text-emerald-700 shrink-0"
                      aria-label={`Toggle ${item.item}`}
                    >
                      {isChecked ? (
                        <FiCheckSquare size={18} className="text-emerald-700 fill-emerald-100" />
                      ) : (
                        <FiSquare size={18} className="text-slate-400" />
                      )}
                    </button>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-bold leading-tight ${
                            isChecked ? "line-through text-slate-400" : "text-slate-900"
                          }`}
                        >
                          {item.item}
                        </span>
                        {item.essential && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded-md bg-rose-100 text-rose-800 font-bold uppercase">
                            Essential
                          </span>
                        )}
                      </div>
                      {item.note && (
                        <p className={`text-[11px] mt-0.5 ${isChecked ? "text-slate-400" : "text-slate-500"}`}>
                          {item.note}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
            <span className="text-xs text-slate-500">
              💡 State is automatically saved on this device.
            </span>
            <button
              type="button"
              onClick={onClose}
              className="ny-btn ny-btn-primary px-6 py-2 text-xs font-bold rounded-xl"
            >
              Done
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
