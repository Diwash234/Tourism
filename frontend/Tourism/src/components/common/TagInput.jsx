import { useState, useRef } from "react"
import { FiX, FiPlus } from "react-icons/fi"

/**
 * Tag input component — allows users to add/remove tags with keyboard support.
 */
export default function TagInput({ tags = [], onChange, placeholder = "Add tag...", maxTags = 10, className = "" }) {
  const [input, setInput] = useState("")
  const inputRef = useRef(null)

  const addTag = (tag) => {
    const trimmed = tag.trim()
    if (!trimmed || tags.includes(trimmed) || tags.length >= maxTags) return
    onChange?.([...tags, trimmed])
    setInput("")
  }

  const removeTag = (tag) => {
    onChange?.(tags.filter(t => t !== tag))
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      addTag(input)
    } else if (e.key === "Backspace" && !input && tags.length > 0) {
      removeTag(tags[tags.length - 1])
    }
  }

  return (
    <div
      className={`flex flex-wrap items-center gap-1.5 p-2 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 focus-within:ring-2 focus-within:ring-emerald-500 focus-within:border-transparent ${className}`}
      onClick={() => inputRef.current?.focus()}
    >
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-[var(--ny-soft-green)] text-[var(--ny-green)]"
        >
          {tag}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); removeTag(tag) }}
            className="p-0.5 rounded-full hover:bg-emerald-100 dark:hover:bg-emerald-900/30"
            aria-label={`Remove ${tag}`}
          >
            <FiX size={12} />
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => addTag(input)}
        placeholder={tags.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[100px] text-sm bg-transparent outline-none text-gray-700 dark:text-gray-300 placeholder:text-gray-400"
      />
      {input && (
        <button
          type="button"
          onClick={() => addTag(input)}
          className="p-1 rounded-lg text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"
          aria-label="Add tag"
        >
          <FiPlus size={14} />
        </button>
      )}
    </div>
  )
}
