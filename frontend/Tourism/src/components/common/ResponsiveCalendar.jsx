import { useState } from 'react'
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Calendar component that adapts to different screen sizes.
 * - Mobile: Compact calendar with swipe support
 * - Tablet/Desktop: Full calendar with month view
 */
const ResponsiveCalendar = ({
  selectedDate,
  onDateChange,
  minDate,
  maxDate,
  className = '',
}) => {
  const [currentMonth, setCurrentMonth] = useState(
    selectedDate ? new Date(selectedDate) : new Date()
  )
  const { isMobile } = useResponsive()

  const daysInMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth() + 1,
    0
  ).getDate()

  const firstDayOfMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth(),
    1
  ).getDay()

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const dayNames = isMobile ? ['S', 'M', 'T', 'W', 'T', 'F', 'S'] : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
  }

  const isDateDisabled = (date) => {
    const d = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), date)
    if (minDate && d < new Date(minDate)) return true
    if (maxDate && d > new Date(maxDate)) return true
    return false
  }

  const isDateSelected = (date) => {
    if (!selectedDate) return false
    const d = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), date)
    return d.toDateString() === new Date(selectedDate).toDateString()
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={prevMonth}
          className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          aria-label="Previous month"
        >
          <FiChevronLeft className="w-5 h-5" />
        </button>
        <h3 className="font-semibold">
          {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
        </h3>
        <button
          onClick={nextMonth}
          className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          aria-label="Next month"
        >
          <FiChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Day names */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {dayNames.map((day, index) => (
          <div key={index} className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Days */}
      <div className="grid grid-cols-7 gap-1">
        {/* Empty cells for days before the first day of the month */}
        {Array.from({ length: firstDayOfMonth }).map((_, index) => (
          <div key={`empty-${index}`} />
        ))}

        {/* Days of the month */}
        {Array.from({ length: daysInMonth }).map((_, index) => {
          const day = index + 1
          const disabled = isDateDisabled(day)
          const selected = isDateSelected(day)

          return (
            <button
              key={day}
              onClick={() => !disabled && onDateChange(new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day))}
              disabled={disabled}
              className={`aspect-square flex items-center justify-center rounded-lg text-sm transition-colors ${
                selected
                  ? 'bg-emerald-600 text-white'
                  : disabled
                  ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {day}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default ResponsiveCalendar
