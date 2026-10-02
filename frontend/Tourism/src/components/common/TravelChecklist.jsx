import { useState, useEffect } from "react"
import { FiCheck, FiPlus, FiTrash2 } from "react-icons/fi"

const DEFAULT_ITEMS = [
  { id: 1, text: "Passport & Visa", category: "Documents", checked: false },
  { id: 2, text: "Travel Insurance", category: "Documents", checked: false },
  { id: 3, text: "Flight Tickets", category: "Documents", checked: false },
  { id: 4, text: "Hotel Bookings", category: "Documents", checked: false },
  { id: 5, text: "First Aid Kit", category: "Health", checked: false },
  { id: 6, text: "Prescription Medicines", category: "Health", checked: false },
  { id: 7, text: "Sunscreen & Sunglasses", category: "Health", checked: false },
  { id: 8, text: "Power Bank", category: "Electronics", checked: false },
  { id: 9, text: "Camera", category: "Electronics", checked: false },
  { id: 10, text: "Universal Adapter", category: "Electronics", checked: false },
  { id: 11, text: "Comfortable Walking Shoes", category: "Clothing", checked: false },
  { id: 12, text: "Rain Jacket", category: "Clothing", checked: false },
  { id: 13, text: "Local Currency", category: "Finance", checked: false },
  { id: 14, text: "Credit/Debit Cards", category: "Finance", checked: false },
  { id: 15, text: "Guidebook / Maps", category: "Misc", checked: false },
  { id: 16, text: "Reusable Water Bottle", category: "Misc", checked: false },
]

const CATEGORIES = ["All", "Documents", "Health", "Electronics", "Clothing", "Finance", "Misc"]

/**
 * Interactive travel checklist with categories, progress tracking,
 * and localStorage persistence.
 */
export default function TravelChecklist() {
  const [items, setItems] = useState(() => {
    try {
      const stored = localStorage.getItem("ny-travel-checklist")
      return stored ? JSON.parse(stored) : DEFAULT_ITEMS
    } catch {
      return DEFAULT_ITEMS
    }
  })
  const [activeCategory, setActiveCategory] = useState("All")
  const [newItemText, setNewItemText] = useState("")
  const [newItemCategory, setNewItemCategory] = useState("Misc")

  useEffect(() => {
    localStorage.setItem("ny-travel-checklist", JSON.stringify(items))
  }, [items])

  const toggleItem = (id) => {
    setItems(prev => prev.map(item => item.id === id ? { ...item, checked: !item.checked } : item))
  }

  const addItem = () => {
    if (!newItemText.trim()) return
    const newItem = {
      id: Date.now(),
      text: newItemText.trim(),
      category: newItemCategory,
      checked: false,
    }
    setItems(prev => [...prev, newItem])
    setNewItemText("")
  }

  const removeItem = (id) => {
    setItems(prev => prev.filter(item => item.id !== id))
  }

  const resetAll = () => {
    setItems(prev => prev.map(item => ({ ...item, checked: false })))
  }

  const filtered = activeCategory === "All" ? items : items.filter(item => item.category === activeCategory)
  const completedCount = items.filter(item => item.checked).length
  const progress = items.length > 0 ? Math.round((completedCount / items.length) * 100) : 0

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Travel Checklist</h3>
        <span className="text-xs font-bold text-[var(--ny-green)]">{progress}%</span>
      </div>

      {/* Progress Bar */}
      <div className="h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden mb-4">
        <div
          className="h-full bg-gradient-to-r from-[var(--ny-green)] to-[var(--ny-mint)] rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Category Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-2 mb-3">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${
              activeCategory === cat
                ? "bg-[var(--ny-green)] text-white"
                : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Items List */}
      <div className="space-y-1.5 max-h-64 overflow-y-auto">
        {filtered.map(item => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors group"
          >
            <button
              type="button"
              onClick={() => toggleItem(item.id)}
              className={`flex h-5 w-5 items-center justify-center rounded-md border-2 transition-all ${
                item.checked
                  ? "bg-[var(--ny-green)] border-[var(--ny-green)] text-white"
                  : "border-gray-300 dark:border-slate-600 hover:border-[var(--ny-green)]"
              }`}
              aria-label={item.checked ? "Uncheck item" : "Check item"}
            >
              {item.checked && <FiCheck size={12} />}
            </button>
            <span className={`flex-1 text-sm ${item.checked ? "line-through text-gray-400 dark:text-gray-500" : "text-gray-700 dark:text-gray-300"}`}>
              {item.text}
            </span>
            <button
              type="button"
              onClick={() => removeItem(item.id)}
              className="p-1 rounded text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
              aria-label="Remove item"
            >
              <FiTrash2 size={12} />
            </button>
          </div>
        ))}
      </div>

      {/* Add Item */}
      <div className="flex gap-2 mt-4 pt-4 border-t border-[var(--ny-border)]">
        <input
          type="text"
          value={newItemText}
          onChange={(e) => setNewItemText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addItem()}
          placeholder="Add custom item..."
          className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <select
          value={newItemCategory}
          onChange={(e) => setNewItemCategory(e.target.value)}
          className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          {CATEGORIES.filter(c => c !== "All").map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={addItem}
          disabled={!newItemText.trim()}
          className="px-3 py-2 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors disabled:opacity-50"
        >
          <FiPlus size={16} />
        </button>
      </div>

      {/* Reset */}
      <div className="flex justify-end mt-3">
        <button
          type="button"
          onClick={resetAll}
          className="text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          Reset all
        </button>
      </div>
    </div>
  )
}
