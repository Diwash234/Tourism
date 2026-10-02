import { useEffect, useState } from 'react'

/**
 * Keyboard Shortcuts hook for handling keyboard navigation.
 * Provides consistent keyboard support across all devices.
 */
export const useKeyboardShortcuts = (shortcuts) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts when typing in inputs
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return
      }

      for (const shortcut of shortcuts) {
        const { key, ctrl, shift, alt, action } = shortcut

        const keyMatch = e.key.toLowerCase() === key.toLowerCase()
        const ctrlMatch = ctrl ? e.ctrlKey || e.metaKey : !(e.ctrlKey || e.metaKey)
        const shiftMatch = shift ? e.shiftKey : !e.shiftKey
        const altMatch = alt ? e.altKey : !e.altKey

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          e.preventDefault()
          action()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}

/**
 * Hook for focus trap in modals.
 */
export const useFocusTrap = (isActive) => {
  const [_focusableElements, _setFocusableElements] = useState([])

  useEffect(() => {
    if (!isActive) return

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return

      const focusable = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )

      const firstElement = focusable[0]
      const lastElement = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault()
          firstElement.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isActive])
}

/**
 * Hook for escape key handling.
 */
export const useEscapeKey = (onEscape, isActive = true) => {
  useEffect(() => {
    if (!isActive) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onEscape()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onEscape, isActive])
}

/**
 * Hook for arrow key navigation.
 */
export const useArrowNavigation = (items, onSelect, isActive = true) => {
  const [selectedIndex, setSelectedIndex] = useState(0)

  useEffect(() => {
    if (!isActive || !items.length) return

    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          e.preventDefault()
          setSelectedIndex((prev) => (prev + 1) % items.length)
          break
        case 'ArrowUp':
        case 'ArrowLeft':
          e.preventDefault()
          setSelectedIndex((prev) => (prev - 1 + items.length) % items.length)
          break
        case 'Enter':
        case ' ':
          e.preventDefault()
          onSelect(items[selectedIndex])
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [items, selectedIndex, onSelect, isActive])

  return selectedIndex
}

/**
 * Hook for keyboard shortcuts help modal.
 */
export const useShortcutsModal = () => {
  const [isOpen, setIsOpen] = useState(false)

  const openModal = () => setIsOpen(true)
  const closeModal = () => setIsOpen(false)

  useEscapeKey(closeModal, isOpen)

  return { isOpen, openModal, closeModal }
}

export default useKeyboardShortcuts
