import React from "react"
import { FiHelpCircle } from "react-icons/fi"

/**
 * Safe icon wrapper that renders a fallback if the primary icon fails.
 * Usage: <SafeIcon icon={FiMapPin} size={16} className="text-ny-green" />
 */
export const SafeIcon = ({ icon: Icon, fallback = FiHelpCircle, ...props }) => {
  try {
    if (!Icon) return <Fallback {...props} />
    return <Icon {...props} />
  } catch {
    return <Fallback {...props} />
  }
}

/**
 * Pre-validated icon map — use this when you need to look up an icon by
 * key from API data. Returns a safe fallback for unknown keys.
 */
export const getIcon = (key, iconMap, fallback = FiHelpCircle) => {
  return iconMap[key] || fallback
}

export default SafeIcon
