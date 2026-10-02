import { useState } from 'react'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Chart component that adapts to different screen sizes.
 * - Mobile: Simplified chart with touch-friendly tooltips
 * - Tablet/Desktop: Full chart with hover tooltips
 */
const ResponsiveChart = ({
  data,
  type = 'bar',
  title,
  xKey,
  yKey,
  color = '#10b981',
  height,
  className = '',
}) => {
  const [activeIndex, setActiveIndex] = useState(null)
  const { isMobile } = useResponsive()

  const chartHeight = height || (isMobile ? 200 : 300)
  const maxValue = Math.max(...data.map((d) => d[yKey] || 0))

  if (type === 'bar') {
    return (
      <div className={className}>
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
        <div className="flex items-end gap-2" style={{ height: chartHeight }}>
          {data.map((item, index) => {
            const value = item[yKey] || 0
            const barHeight = (value / maxValue) * (chartHeight - 40)

            return (
              <div
                key={index}
                className="flex-1 flex flex-col items-center gap-1"
                onMouseEnter={() => !isMobile && setActiveIndex(index)}
                onMouseLeave={() => !isMobile && setActiveIndex(null)}
                onClick={() => isMobile && setActiveIndex(activeIndex === index ? null : index)}
              >
                <div
                  className="w-full rounded-t transition-all duration-200"
                  style={{
                    height: barHeight,
                    backgroundColor: color,
                    opacity: activeIndex === null || activeIndex === index ? 1 : 0.5,
                  }}
                />
                <span className="text-xs text-gray-500 truncate w-full text-center">
                  {item[xKey]}
                </span>
              </div>
            )
          })}
        </div>
        {activeIndex !== null && (
          <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
            <span className="font-medium">{data[activeIndex][xKey]}:</span> {data[activeIndex][yKey]}
          </div>
        )}
      </div>
    )
  }

  if (type === 'line') {
    const points = data.map((item, index) => {
      const x = (index / (data.length - 1)) * 100
      const y = 100 - ((item[yKey] || 0) / maxValue) * 100
      return `${x},${y}`
    }).join(' ')

    return (
      <div className={className}>
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
        <svg
          viewBox="0 0 100 100"
          className="w-full"
          style={{ height: chartHeight }}
          preserveAspectRatio="none"
        >
          <polyline
            points={points}
            fill="none"
            stroke={color}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
          {data.map((item, index) => {
            const x = (index / (data.length - 1)) * 100
            const y = 100 - ((item[yKey] || 0) / maxValue) * 100
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="2"
                fill={color}
                className="cursor-pointer"
                onMouseEnter={() => !isMobile && setActiveIndex(index)}
                onClick={() => isMobile && setActiveIndex(activeIndex === index ? null : index)}
              />
            )
          })}
        </svg>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{data[0]?.[xKey]}</span>
          <span>{data[data.length - 1]?.[xKey]}</span>
        </div>
        {activeIndex !== null && (
          <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
            <span className="font-medium">{data[activeIndex][xKey]}:</span> {data[activeIndex][yKey]}
          </div>
        )}
      </div>
    )
  }

  if (type === 'pie') {
    const total = data.reduce((sum, d) => sum + (d[yKey] || 0), 0)
    // Precompute each slice's angle and cumulative start angle as pure prefix
    // sums (identical left-to-right accumulation as before, without mutating a
    // variable after render completes).
    const sliceAngles = data.map((d) => ((d[yKey] || 0) / total) * 360)
    const startAngles = sliceAngles.map((_, index) =>
      sliceAngles.slice(0, index).reduce((sum, angle) => sum + angle, 0)
    )

    return (
      <div className={className}>
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
        <div className="flex items-center gap-4">
          <svg viewBox="0 0 100 100" className="w-32 h-32">
            {data.map((item, index) => {
              const angle = sliceAngles[index]
              const startAngle = startAngles[index]

              const startRad = (startAngle * Math.PI) / 180
              const endRad = ((startAngle + angle) * Math.PI) / 180

              const x1 = 50 + 40 * Math.cos(startRad)
              const y1 = 50 + 40 * Math.sin(startRad)
              const x2 = 50 + 40 * Math.cos(endRad)
              const y2 = 50 + 40 * Math.sin(endRad)

              const largeArc = angle > 180 ? 1 : 0

              const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

              return (
                <path
                  key={index}
                  d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                  fill={colors[index % colors.length]}
                  className="cursor-pointer hover:opacity-80"
                  onMouseEnter={() => !isMobile && setActiveIndex(index)}
                  onClick={() => isMobile && setActiveIndex(activeIndex === index ? null : index)}
                />
              )
            })}
          </svg>
          <div className="space-y-1">
            {data.map((item, index) => {
              const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
              return (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: colors[index % colors.length] }} />
                  <span>{item[xKey]}</span>
                </div>
              )
            })}
          </div>
        </div>
        {activeIndex !== null && (
          <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
            <span className="font-medium">{data[activeIndex][xKey]}:</span> {data[activeIndex][yKey]}
          </div>
        )}
      </div>
    )
  }

  return null
}

export default ResponsiveChart
