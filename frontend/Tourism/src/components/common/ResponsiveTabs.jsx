import { useState } from 'react'
import 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Tabs component that adapts to different screen sizes.
 * - Mobile: Horizontal scrollable tabs with swipe support
 * - Tablet/Desktop: Full tab bar with dropdown for overflow
 */
const ResponsiveTabs = ({
  tabs,
  defaultTab,
  onChange,
  variant = 'underline',
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id)
  const [_scrollPosition, _setScrollPosition] = useState(0)
  const { isMobile } = useResponsive()

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    onChange?.(tabId)
  }

  const variants = {
    underline: {
      container: 'border-b border-gray-200 dark:border-gray-700',
      tab: (isActive) =>
        `px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
          isActive
            ? 'border-emerald-600 text-emerald-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
        }`,
    },
    pills: {
      container: 'bg-gray-100 dark:bg-gray-800 rounded-lg p-1',
      tab: (isActive) =>
        `px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
          isActive
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
        }`,
    },
    cards: {
      container: 'grid gap-2',
      tab: (isActive) =>
        `px-4 py-3 text-sm font-medium rounded-lg border transition-colors ${
          isActive
            ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
            : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
        }`,
    },
  }

  const style = variants[variant] || variants.underline

  return (
    <div className={className}>
      <div
        className={`${style.container} ${
          isMobile ? 'flex overflow-x-auto scrollbar-hide' : variant === 'cards' ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'flex'
        }`}
        role="tablist"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`${style.tab(activeTab === tab.id)} ${
              isMobile ? 'flex-shrink-0' : ''
            }`}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="mt-4">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            id={`panel-${tab.id}`}
            role="tabpanel"
            aria-labelledby={tab.id}
            className={activeTab === tab.id ? 'block' : 'hidden'}
          >
            {tab.content}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ResponsiveTabs
