import { useState, useRef } from "react"
import { FiGripVertical } from "react-icons/fi"

/**
 * Drag and drop list component using native HTML5 drag events.
 * Supports reordering items with visual feedback.
 */
export default function DraggableList({ items, onReorder, renderItem, className = "" }) {
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [overIndex, setOverIndex] = useState(null)
  const dragNode = useRef(null)

  const handleDragStart = (e, index) => {
    dragNode.current = e.target
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = "move"
    // Required for Firefox
    e.dataTransfer.setData("text/plain", "")
  }

  const handleDragOver = (e, index) => {
    e.preventDefault()
    if (overIndex !== index) setOverIndex(index)
  }

  const handleDrop = (e, index) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) {
      setDraggedIndex(null)
      setOverIndex(null)
      return
    }
    const newItems = [...items]
    const [moved] = newItems.splice(draggedIndex, 1)
    newItems.splice(index, 0, moved)
    onReorder?.(newItems)
    setDraggedIndex(null)
    setOverIndex(null)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
    setOverIndex(null)
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {items.map((item, i) => (
        <div
          key={item.id || i}
          draggable
          onDragStart={(e) => handleDragStart(e, i)}
          onDragOver={(e) => handleDragOver(e, i)}
          onDrop={(e) => handleDrop(e, i)}
          onDragEnd={handleDragEnd}
          className={`flex items-center gap-2 p-3 rounded-xl border bg-white dark:bg-slate-800 transition-all ${
            draggedIndex === i
              ? "opacity-50 border-emerald-400 shadow-lg scale-[1.02]"
              : overIndex === i
              ? "border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/20"
              : "border-[var(--ny-border)]"
          }`}
        >
          <span className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1">
            <FiGripVertical size={16} />
          </span>
          <div className="flex-1 min-w-0">{renderItem(item, i)}</div>
        </div>
      ))}
    </div>
  )
}
