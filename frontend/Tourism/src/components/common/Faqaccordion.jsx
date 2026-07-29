import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { FiChevronDown } from "react-icons/fi"

/**
 * FAQAccordion
 * Classic "click the chevron to reveal/collapse the answer" pattern.
 * Only one item open at a time (typical FAQ UX) — pass allowMultiple
 * if you want independent toggles instead.
 *
 * items: [{ question: string, answer: string }]
 */
const FAQAccordion = ({ items = [], allowMultiple = false }) => {
  const [openIndexes, setOpenIndexes] = useState(() => new Set())

  const toggle = (index) => {
    setOpenIndexes((prev) => {
      const next = allowMultiple ? new Set(prev) : new Set()
      if (prev.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => {
        const isOpen = openIndexes.has(index)
        return (
          <div key={item.question} className="card-base overflow-hidden">
            <button
              type="button"
              onClick={() => toggle(index)}
              aria-expanded={isOpen}
              className="w-full flex items-center justify-between gap-4 text-left px-5 py-4"
            >
              <span className="font-semibold text-dark text-sm sm:text-base">{item.question}</span>
              <motion.span
                animate={{ rotate: isOpen ? 180 : 0 }}
                transition={{ duration: 0.2 }}
                className={`shrink-0 p-1.5 rounded-full ${isOpen ? "bg-himalaya-500 text-white" : "bg-gray-100 text-gray-500"}`}
              >
                <FiChevronDown size={16} />
              </motion.span>
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  key="content"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <p className="px-5 pb-4 text-sm text-gray-500 leading-relaxed">{item.answer}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}

export default FAQAccordion