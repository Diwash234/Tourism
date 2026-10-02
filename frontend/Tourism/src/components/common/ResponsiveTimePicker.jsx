import { useState } from 'react'
import { FiClock } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Time Picker component that adapts to different screen sizes.
 * - Mobile: Native time input
 * - Tablet/Desktop: Custom time picker with hour/minute selection
 */
const ResponsiveTimePicker = ({
  value,
  onChange,
  placeholder = 'Select time',
  minTime,
  maxTime,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { isMobile } = useResponsive()

  // Mobile: Use native time input
  if (isMobile) {
    return (
      <div className={`relative ${className}`}>
        <FiClock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="time"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          min={minTime}
          max={maxTime}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
        />
      </div>
    )
  }

  // Desktop: Custom time picker
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const minutes = Array.from({ length: 60 }, (_, i) => i)

  const selectedHour = value ? parseInt(value.split(':')[0]) : null
  const selectedMinute = value ? parseInt(value.split(':')[1]) : null

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100 text-left"
      >
        <FiClock className="w-5 h-5 text-gray-400" />
        <span className={value ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'}>
          {value || placeholder}
        </span>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute z-50 mt-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg p-4">
            <div className="flex gap-4">
              {/* Hours */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Hour</label>
                <select
                  value={selectedHour || ''}
                  onChange={(e) => onChange(`${e.target.value}:${selectedMinute || '00'}`)}
                  className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="">--</option>
                  {hours.map((h) => (
                    <option key={h} value={h.toString().padStart(2, '0')}>
                      {h.toString().padStart(2, '0')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Minutes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Minute</label>
                <select
                  value={selectedMinute || ''}
                  onChange={(e) => onChange(`${selectedHour || '00'}:${e.target.value}`)}
                  className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="">--</option>
                  {minutes.map((m) => (
                    <option key={m} value={m.toString().padStart(2, '0')}>
                      {m.toString().padStart(2, '0')}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                Done
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ResponsiveTimePicker
