/**
 * Responsive grid that automatically adjusts columns based on content.
 */
export default function ResponsiveGrid({ children, minItemWidth = 280, gap = 16, className = "" }) {
  return (
    <div
      className={`grid ${className}`}
      style={{
        gridTemplateColumns: `repeat(auto-fill, minmax(${minItemWidth}px, 1fr))`,
        gap: `${gap}px`,
      }}
    >
      {children}
    </div>
  )
}
